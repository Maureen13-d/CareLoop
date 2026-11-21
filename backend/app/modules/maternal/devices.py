"""Hub and band ingestion. The server recomputes the level. Devices never diagnose.

SMS text stays short and discreet. Audit rows store labels, not free text.
"""

import time
from datetime import datetime

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.config import REPO_ROOT
from app.core.errors import DomainError
from app.core.security import verify_password
from app.modules.audit import service as audit
from app.modules.auth.models import ROLE_CHW, User
from app.modules.channels.models import SmsMessage
from app.modules.maternal.models import BandCommand, BandEvent, Device, Pregnancy, Reading
from app.modules.maternal.service import open_maternal_case
from app.modules.maternal.triage import triage_maternal
from app.modules.pathways.service import find_open_case, transition
from app.modules.patients.models import Patient
from app.modules.tasks.models import NavigatorTask
from app.modules.tasks.service import create_task

PROTEIN_CODE = {"0": "neg", "t": "trace", "1": "1+", "2": "2+", "3": "3+", "u": "unknown"}
SIGN_CODE = {
    "H": "headache_severe",
    "S": "vision_blurred",
    "B": "heavy_bleeding",
    "C": "convulsion",
    "A": "severe_abdominal_pain",
    "D": "difficulty_breathing",
    "F": "no_fetal_movement",
    "W": "fever_severe_weakness",
    "L": "leaking_fluid_fever",
    "E": "swelling_face_hands",
    "M": "reduced_fetal_movement",
}
NAVIGATOR_SMS = "Desk: a check needs a person now."
CONTACT_SMS = "Please go to the nearest clinic now."
_HITS: dict[str, list[float]] = {}


def load_band_rules() -> dict:
    path = REPO_ROOT / "rules" / "band_nudges.yaml"
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def checksum(body: str) -> str:
    return f"{sum(ord(char) for char in body) % 256:02x}"


def _norm_id(value: str) -> str:
    return value.replace("-", "").upper()


def find_device(db: Session, raw_id: str) -> Device | None:
    want = _norm_id(raw_id)
    for device in db.scalars(select(Device)).all():
        if _norm_id(device.pseudonymous_device_id) == want:
            return device
    return None


def rate_limit(device_id: str) -> None:
    now = time.monotonic()
    hits = [stamp for stamp in _HITS.get(device_id, []) if now - stamp < 60]
    if len(hits) >= 60:
        raise DomainError(429, "rate_limited", "Too many device messages. Try again shortly.")
    hits.append(now)
    _HITS[device_id] = hits


def reset_rate_limit() -> None:
    _HITS.clear()


def authenticate(db: Session, device_id: str, key: str | None) -> Device:
    device = find_device(db, device_id)
    if device is None or not key or not verify_password(key, device.api_key_hash):
        raise DomainError(401, "not_authenticated", "Device key was not accepted")
    rate_limit(device.pseudonymous_device_id)
    device.last_seen_at = clock.now()
    return device


def parse_sms(text: str) -> dict:
    """R|device|seq|sys|dia|pulse|protein|signs|checksum. Reject anything that does not parse."""
    parts = (text or "").strip().split("|")
    if len(parts) != 9 or parts[0] != "R":
        raise DomainError(422, "bad_sms", "The message is not a device reading")
    body = "|".join(parts[:-1])
    if checksum(body) != parts[-1].lower():
        raise DomainError(422, "bad_checksum", "The message checksum does not match")
    device_id, seq, sys_s, dia_s, pulse_s, protein, signs = parts[1:8]
    if protein not in PROTEIN_CODE:
        raise DomainError(422, "bad_sms", "The protein code is not recognised")
    if not seq.isdigit() or not sys_s.isdigit() or not dia_s.isdigit() or not pulse_s.isdigit():
        raise DomainError(422, "bad_sms", "A number field is not digits")
    decoded = []
    for mark in signs:
        if mark not in SIGN_CODE:
            raise DomainError(422, "bad_sms", "A sign code is not recognised")
        decoded.append(SIGN_CODE[mark])
    return {
        "device_id": device_id,
        "seq": seq,
        "systolic": int(sys_s),
        "diastolic": int(dia_s),
        "pulse": int(pulse_s),
        "urine_protein": PROTEIN_CODE[protein],
        "hb_band": "unknown",
        "danger_signs": decoded,
        "hub_local_level": None,
    }


def _pregnancy_for_ref(db: Session, pregnancy_ref: str) -> tuple[Patient, Pregnancy]:
    patient = db.scalar(select(Patient).where(Patient.patient_ref == pregnancy_ref))
    if patient is None:
        raise DomainError(404, "not_found", "No booklet matches that reference")
    pregnancy = db.scalar(
        select(Pregnancy).where(Pregnancy.patient_id == patient.id).order_by(Pregnancy.id.desc())
    )
    if pregnancy is None:
        raise DomainError(404, "not_found", "No pregnancy is linked to that booklet")
    return patient, pregnancy


def _existing_reading(db: Session, device: Device | None, pregnancy: Pregnancy, client_id: str):
    if device is not None:
        return db.scalar(
            select(Reading).where(
                Reading.device_id == device.id, Reading.client_reading_id == client_id
            )
        )
    return db.scalar(
        select(Reading).where(
            Reading.pregnancy_id == pregnancy.id,
            Reading.device_id.is_(None),
            Reading.client_reading_id == client_id,
        )
    )


def _result(reading: Reading, case_id: int | None, duplicate: bool) -> dict:
    return {
        "reading_id": reading.id,
        "level": reading.risk_level,
        "case_id": case_id,
        "duplicate": duplicate,
    }


HUB_SUMMARY = {
    "yellow": "A home reading was labelled yellow. A navigator may call. "
    "Decision support only. PENDING CLINICAL REVIEW.",
    "red": "A home reading was labelled red. The person was told to go to a clinic now. "
    "Decision support only. PENDING CLINICAL REVIEW.",
}


def _flag_case(db: Session, patient: Patient, pregnancy: Pregnancy, level: str):
    case = find_open_case(db, patient.id, "maternal")
    if case is None:
        case = open_maternal_case(db, patient, pregnancy, None, urgency="routine")
    if case.state == "enrolled":
        case = transition(db, case, "home_screened", None, "Home check recorded")
    if case.state == "home_screened":
        if level == "red":
            case.urgency = "urgent"
        case = transition(db, case, "risk_flagged", None, "Decision support flagged a check")
    elif level == "red":
        case.urgency = "urgent"
    priority = "urgent" if level == "red" else "normal"
    task = create_task(
        db,
        task_type="maternal_warning",
        priority=priority,
        case_id=case.id,
        source="device",
    )
    if level == "red" and task.priority != "urgent":
        task.priority = "urgent"
    # Say which colour it was, so yellow and red read differently on the navigator's page.
    # A later yellow never softens an open red.
    if level == "red" or task.priority != "urgent":
        task.summary = HUB_SUMMARY[level]
    db.commit()
    return case


def ingest_reading(
    db: Session,
    *,
    device: Device | None,
    pregnancy_ref: str,
    client_reading_id: str,
    systolic,
    diastolic,
    pulse,
    urine_protein,
    hb_band,
    danger_signs: list,
    hub_local_level: str | None,
    source: str,
    taken_at: datetime | None = None,
) -> dict:
    if device is not None and device.kind != "hub":
        raise DomainError(409, "wrong_device", "Readings come from a hub, not a band")
    patient, pregnancy = _pregnancy_for_ref(db, pregnancy_ref)
    existing = _existing_reading(db, device, pregnancy, client_reading_id)
    if existing is not None:
        case = find_open_case(db, patient.id, "maternal")
        return _result(existing, case.id if case else None, True)

    taken = taken_at or clock.now()
    decision = triage_maternal(
        {
            "systolic": systolic,
            "diastolic": diastolic,
            "pulse": pulse,
            "urine_protein": urine_protein,
            "hb_band": hb_band,
            "taken_at": taken,
            "gestation_band": pregnancy.gestation_band,
        },
        danger_signs,
        {"now": clock.now(), "gestation_band": pregnancy.gestation_band},
    )
    mismatch = bool(hub_local_level) and hub_local_level != decision["level"]
    reading = Reading(
        pregnancy_id=pregnancy.id,
        device_id=device.id if device else None,
        client_reading_id=client_reading_id,
        systolic=systolic if isinstance(systolic, int) else None,
        diastolic=diastolic if isinstance(diastolic, int) else None,
        pulse=pulse if isinstance(pulse, int) else None,
        urine_protein=urine_protein if isinstance(urine_protein, str) else None,
        hb_band=hb_band if isinstance(hb_band, str) else None,
        danger_signs=list(danger_signs or []),
        risk_level=decision["level"],
        hub_local_level=hub_local_level,
        level_mismatch=mismatch,
        rule_ids=decision["rule_ids"],
        rules_version=decision["rules_version"],
        source=source,
        taken_at=taken,
        received_at=clock.now(),
    )
    db.add(reading)
    db.flush()
    audit.record(
        db,
        actor=None,
        action="reading.received",
        entity_type="reading",
        entity_id=reading.id,
        patient_id=patient.id,
        detail={"level": decision["level"], "rules": decision["rule_ids"], "source": source},
    )
    if mismatch:
        audit.record(
            db,
            actor=None,
            action="reading.level_mismatch",
            entity_type="reading",
            entity_id=reading.id,
            patient_id=patient.id,
            detail={"hub": hub_local_level, "server": decision["level"]},
        )
    case_id = None
    if decision["level"] in {"yellow", "red"}:
        case = _flag_case(db, patient, pregnancy, decision["level"])
        case_id = case.id
    else:
        db.commit()
    return _result(reading, case_id, False)


def _queue_sms(db: Session, phone_ref: str, body: str) -> None:
    db.add(
        SmsMessage(
            phone_ref=phone_ref,
            direction="out",
            body=body,
            status="queued",
            created_at=clock.now(),
        )
    )


def _commands(db: Session, device: Device) -> list[dict]:
    rows = db.scalars(
        select(BandCommand)
        .where(BandCommand.device_id == device.id, BandCommand.acked_at.is_(None))
        .order_by(BandCommand.id)
    ).all()
    return [{"id": row.id, "kind": row.kind} for row in rows]


def _add_command(db: Session, device: Device, kind: str) -> None:
    db.add(BandCommand(device_id=device.id, kind=kind, created_at=clock.now()))


def ingest_band_event(db: Session, device: Device, body: dict) -> dict:
    if device.kind != "band":
        raise DomainError(409, "wrong_device", "This event is for a band")
    event_id = body["event_id"]
    existing = db.scalar(
        select(BandEvent).where(BandEvent.device_id == device.id, BandEvent.event_id == event_id)
    )
    if existing is not None:
        return {"event_id": existing.id, "duplicate": True, "commands": _commands(db, device)}
    pregnancy = (
        db.get(Pregnancy, device.assigned_pregnancy_id) if device.assigned_pregnancy_id else None
    )
    if pregnancy is None:
        raise DomainError(409, "not_lent", "This band is not lent to anyone")
    patient = db.get(Patient, pregnancy.patient_id)
    kind = body["type"]
    when = body.get("ts") or clock.now()
    if isinstance(when, str):
        when = datetime.fromisoformat(when).replace(tzinfo=None)
    db.add(
        BandEvent(
            device_id=device.id,
            pregnancy_id=pregnancy.id,
            event_id=event_id,
            type=kind,
            hr=body.get("hr"),
            spo2=body.get("spo2"),
            ts=when,
            received_at=clock.now(),
        )
    )
    if body.get("battery_pct") is not None:
        device.battery_pct = body["battery_pct"]
    rules = load_band_rules()
    case_id = None
    if kind == "sos":
        case = _flag_case(db, patient, pregnancy, "red")
        case.urgency = "urgent"
        case_id = case.id
        _queue_sms(db, rules["navigator_handset"], NAVIGATOR_SMS)
        if pregnancy.consent_band_contact:
            _queue_sms(db, f"contact-{pregnancy.id}", CONTACT_SMS)
        audit.record(
            db,
            actor=None,
            action="band.sos",
            entity_type="device",
            entity_id=device.id,
            patient_id=patient.id,
            detail={"level": "red"},
        )
        _add_command(db, device, "vibrate")
    elif kind in {"hr_trend", "spo2_low"}:
        create_task(db, task_type="chw_cuff", priority="normal", case_id=None, source="band")
        _add_command(db, device, "vibrate")
        _add_command(db, device, "nudge_reading")
    elif kind == "inactivity":
        _add_command(db, device, "check_in")
    elif kind == "battery_low":
        create_task(db, task_type="chw_battery", priority="normal", case_id=None, source="band")
    elif kind == "ack":
        pending = db.scalar(
            select(BandCommand)
            .where(BandCommand.device_id == device.id, BandCommand.acked_at.is_(None))
            .order_by(BandCommand.id)
        )
        if pending is not None:
            pending.acked_at = clock.now()
    else:
        raise DomainError(422, "bad_event", "That band event type is not recognised")
    db.commit()
    return {
        "event_id": event_id,
        "duplicate": False,
        "case_id": case_id,
        "commands": _commands(db, device),
    }


def pending_commands(db: Session, device: Device) -> list[dict]:
    return _commands(db, device)


def note_offline(db: Session) -> int:
    rules = load_band_rules()
    cutoff_hours = float(rules["offline_hours"])
    now = clock.now()
    opened = 0
    for device in db.scalars(select(Device).where(Device.status.in_(("active", "lent")))).all():
        if device.last_seen_at is None:
            continue
        hours = (now - device.last_seen_at).total_seconds() / 3600
        if hours <= cutoff_hours:
            continue
        existing = db.scalar(
            select(NavigatorTask.id).where(
                NavigatorTask.task_type == "device_offline",
                NavigatorTask.status == "open",
            )
        )
        if existing is not None:
            break
        create_task(
            db, task_type="device_offline", priority="normal", case_id=None, source="device"
        )
        opened += 1
    db.commit()
    return opened


def lend_band(db: Session, actor: User, device: Device, pregnancy: Pregnancy) -> Device:
    if actor.role == ROLE_CHW and pregnancy.assigned_chw_id != actor.id:
        raise DomainError(403, "forbidden", "This person is not assigned to you")
    if device.kind != "band":
        raise DomainError(409, "wrong_device", "Only a band can be lent")
    if not pregnancy.consent_band_contact:
        raise DomainError(
            409, "consent_required", "Band contact consent is required before lending"
        )
    device.assigned_pregnancy_id = pregnancy.id
    device.assigned_chw_id = pregnancy.assigned_chw_id
    device.status = "lent"
    audit.record(
        db,
        actor=actor,
        action="device.lent",
        entity_type="device",
        entity_id=device.id,
        patient_id=pregnancy.patient_id,
        detail={"status": "lent"},
    )
    db.commit()
    return device


def return_band(db: Session, actor: User, device: Device, lost: bool = False) -> Device:
    device.assigned_pregnancy_id = None
    device.status = "lost" if lost else "returned"
    audit.record(
        db,
        actor=actor,
        action="device.lost" if lost else "device.returned",
        entity_type="device",
        entity_id=device.id,
        detail={"status": device.status},
    )
    db.commit()
    return device
