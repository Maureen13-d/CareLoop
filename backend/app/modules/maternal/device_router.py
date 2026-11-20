"""Device routes. Authenticated with X-Device-Key, not a staff login."""

from datetime import datetime

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.maternal import devices

router = APIRouter(prefix="/device", tags=["device"])


class ReadingIn(BaseModel):
    device_id: str
    client_reading_id: str
    pregnancy_ref: str
    taken_at: datetime | None = None
    systolic: int | None = None
    diastolic: int | None = None
    pulse: int | None = None
    urine_protein: str | None = None
    hb_band: str | None = None
    danger_signs: list[str] = Field(default_factory=list)
    hub_local_level: str | None = None


class SmsIn(BaseModel):
    text: str
    pregnancy_ref: str


class BandEventIn(BaseModel):
    device_id: str
    event_id: str
    type: str
    ts: datetime | None = None
    hr: int | None = None
    spo2: int | None = None
    battery_pct: int | None = None


class HeartbeatIn(BaseModel):
    device_id: str
    battery_pct: int | None = None


def _key(x_device_key: str | None = Header(default=None)) -> str | None:
    return x_device_key


@router.post("/readings")
def post_reading(
    data: ReadingIn, db: Session = Depends(get_db), key: str | None = Depends(_key)
):
    device = devices.authenticate(db, data.device_id, key)
    return devices.ingest_reading(
        db,
        device=device,
        pregnancy_ref=data.pregnancy_ref,
        client_reading_id=data.client_reading_id,
        systolic=data.systolic,
        diastolic=data.diastolic,
        pulse=data.pulse,
        urine_protein=data.urine_protein,
        hb_band=data.hb_band,
        danger_signs=data.danger_signs,
        hub_local_level=data.hub_local_level,
        source="hub",
        taken_at=data.taken_at,
    )


@router.post("/sms-ingest")
def post_sms(data: SmsIn, db: Session = Depends(get_db), key: str | None = Depends(_key)):
    parsed = devices.parse_sms(data.text)
    device = devices.authenticate(db, parsed["device_id"], key)
    return devices.ingest_reading(
        db,
        device=device,
        pregnancy_ref=data.pregnancy_ref,
        client_reading_id=f"{device.pseudonymous_device_id}-{parsed['seq']}",
        systolic=parsed["systolic"],
        diastolic=parsed["diastolic"],
        pulse=parsed["pulse"],
        urine_protein=parsed["urine_protein"],
        hb_band=parsed["hb_band"],
        danger_signs=parsed["danger_signs"],
        hub_local_level=None,
        source="sms",
    )


@router.post("/band/events")
def post_band(data: BandEventIn, db: Session = Depends(get_db), key: str | None = Depends(_key)):
    device = devices.authenticate(db, data.device_id, key)
    return devices.ingest_band_event(db, device, data.model_dump())


@router.get("/band/commands")
def get_commands(
    device_id: str, db: Session = Depends(get_db), key: str | None = Depends(_key)
):
    device = devices.authenticate(db, device_id, key)
    return {"commands": devices.pending_commands(db, device)}


@router.post("/heartbeat")
def post_heartbeat(
    data: HeartbeatIn, db: Session = Depends(get_db), key: str | None = Depends(_key)
):
    device = devices.authenticate(db, data.device_id, key)
    if data.battery_pct is not None:
        device.battery_pct = data.battery_pct
    db.commit()
    return {"ok": True, "device_id": device.pseudonymous_device_id}
