"""Hub readings, SMS fallback, and band events. Synthetic devices only."""

from datetime import datetime

from sqlalchemy import func, select

from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.channels.models import SmsMessage
from app.modules.maternal.devices import checksum, parse_sms
from app.modules.maternal.models import Device, Pregnancy, Reading
from app.modules.pathways.models import CareCase
from app.modules.patients.schemas import PatientCreate
from app.modules.patients.service import create_patient
from app.modules.tasks.models import NavigatorTask

KEY = "synthetic-device-key"
KEY_HASH = hash_password(KEY)


def _setup(db, *, band_consent=True):
    chw = db.scalar(select(User).where(User.username == "chw"))
    patient = create_patient(
        db,
        chw,
        PatientCreate(display_name="Mercy Demo", age_band="20-24", zone="Demo Zone Kisumu"),
    )
    pregnancy = Pregnancy(
        patient_id=patient.id,
        gestation_band="28-36w",
        area_label="Demo Zone Kisumu",
        consent_care_coordination=True,
        consent_sms_reminders=True,
        consent_band_contact=band_consent,
        assigned_chw_id=chw.id,
        created_at=datetime(2026, 11, 20, 9, 0),
    )
    db.add(pregnancy)
    hub = Device(
        kind="hub",
        pseudonymous_device_id="HUB-0007",
        api_key_hash=KEY_HASH,
        assigned_chw_id=chw.id,
        status="active",
    )
    band = Device(
        kind="band",
        pseudonymous_device_id="BAND-0012",
        api_key_hash=KEY_HASH,
        assigned_chw_id=chw.id,
        status="active",
    )
    db.add_all([hub, band])
    db.commit()
    db.refresh(pregnancy)
    return patient, pregnancy, hub, band


def _reading(ref, **extra):
    body = {
        "device_id": "HUB-0007",
        "client_reading_id": "HUB-0007-000231",
        "pregnancy_ref": ref,
        "systolic": 152,
        "diastolic": 98,
        "pulse": 88,
        "urine_protein": "2+",
        "hb_band": "unknown",
        "danger_signs": ["headache_severe", "vision_blurred"],
        "hub_local_level": "red",
    }
    body.update(extra)
    return body


def test_reading_opens_one_case_and_a_resend_does_not(client, db_session):
    patient, _, _, _ = _setup(db_session)
    headers = {"X-Device-Key": KEY}
    first = client.post("/api/v1/device/readings", json=_reading(patient.patient_ref), headers=headers)
    assert first.status_code == 200, first.text
    assert first.json()["duplicate"] is False
    assert first.json()["level"] == "red"
    assert first.json()["case_id"]
    second = client.post("/api/v1/device/readings", json=_reading(patient.patient_ref), headers=headers)
    assert second.status_code == 200, second.text
    assert second.json()["duplicate"] is True
    assert second.json()["reading_id"] == first.json()["reading_id"]
    assert db_session.scalar(select(func.count()).select_from(Reading)) == 1
    assert db_session.scalar(select(func.count()).select_from(CareCase)) == 1
    case = db_session.get(CareCase, first.json()["case_id"])
    assert case.state == "risk_flagged"
    assert case.urgency == "urgent"


def test_server_wins_when_the_hub_level_disagrees(client, db_session):
    patient, _, _, _ = _setup(db_session)
    body = _reading(patient.patient_ref, hub_local_level="green", client_reading_id="HUB-0007-9")
    resp = client.post("/api/v1/device/readings", json=body, headers={"X-Device-Key": KEY})
    assert resp.status_code == 200, resp.text
    assert resp.json()["level"] == "red"
    reading = db_session.get(Reading, resp.json()["reading_id"])
    assert reading.level_mismatch is True
    assert reading.hub_local_level == "green"


def test_bad_key_and_wrong_kind_are_refused(client, db_session):
    patient, _, _, _ = _setup(db_session)
    bad = client.post(
        "/api/v1/device/readings",
        json=_reading(patient.patient_ref),
        headers={"X-Device-Key": "nope"},
    )
    assert bad.status_code == 401
    band = client.post(
        "/api/v1/device/readings",
        json=_reading(patient.patient_ref, device_id="BAND-0012"),
        headers={"X-Device-Key": KEY},
    )
    assert band.status_code == 409


def test_sms_checksum_and_a_bad_message(client, db_session):
    patient, _, _, _ = _setup(db_session)
    payload = "R|HUB0007|000231|152|098|088|2|HS"
    good = client.post(
        "/api/v1/device/sms-ingest",
        json={"text": f"{payload}|{checksum(payload)}", "pregnancy_ref": patient.patient_ref},
        headers={"X-Device-Key": KEY},
    )
    assert good.status_code == 200, good.text
    assert good.json()["level"] == "red"
    bad = client.post(
        "/api/v1/device/sms-ingest",
        json={"text": f"{payload}|ff", "pregnancy_ref": patient.patient_ref},
        headers={"X-Device-Key": KEY},
    )
    assert bad.status_code == 422
    assert bad.json()["error"]["code"] == "bad_checksum"
    short = client.post(
        "/api/v1/device/sms-ingest",
        json={"text": "hello", "pregnancy_ref": patient.patient_ref},
        headers={"X-Device-Key": KEY},
    )
    assert short.status_code == 422


def test_sos_opens_one_urgent_case_and_a_nudge_does_not(client, db_session):
    _patient, pregnancy, _, band = _setup(db_session)
    band.assigned_pregnancy_id = pregnancy.id
    band.status = "lent"
    db_session.commit()
    headers = {"X-Device-Key": KEY}
    sos = {
        "device_id": "BAND-0012",
        "event_id": "BAND-0012-000044",
        "type": "sos",
        "hr": 112,
        "spo2": 94,
        "battery_pct": 63,
    }
    first = client.post("/api/v1/device/band/events", json=sos, headers=headers)
    assert first.status_code == 200, first.text
    assert first.json()["duplicate"] is False
    assert first.json()["case_id"]
    again = client.post(
        "/api/v1/device/band/events",
        json={**sos, "event_id": "BAND-0012-000045"},
        headers=headers,
    )
    assert again.status_code == 200, again.text
    assert db_session.scalar(select(func.count()).select_from(CareCase)) == 1
    case = db_session.get(CareCase, first.json()["case_id"])
    assert case.urgency == "urgent"
    texts = db_session.scalars(select(SmsMessage.body)).all()
    assert texts
    assert all("pregnant" not in body.lower() for body in texts)

    nudge = client.post(
        "/api/v1/device/band/events",
        json={"device_id": "BAND-0012", "event_id": "BAND-0012-9", "type": "hr_trend", "hr": 90},
        headers=headers,
    )
    assert nudge.status_code == 200, nudge.text
    assert "case_id" not in nudge.json() or nudge.json().get("case_id") in (None,)
    assert db_session.scalar(select(func.count()).select_from(CareCase)) == 1
    cuff = db_session.scalar(select(NavigatorTask).where(NavigatorTask.task_type == "chw_cuff"))
    assert cuff is not None
    assert cuff.case_id is None
    kinds = {item["kind"] for item in nudge.json()["commands"]}
    assert "nudge_reading" in kinds


def test_parser_rejects_an_unknown_sign():
    payload = "R|HUB0007|000001|120|080|070|0|Z"
    try:
        parse_sms(f"{payload}|{checksum(payload)}")
        raise AssertionError("expected a refusal")
    except Exception as exc:
        assert exc.status_code == 422
