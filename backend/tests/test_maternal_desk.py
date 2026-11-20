"""Maternal desk: readings, one urgent task, simulated fare and cover, clinic milestones."""

import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient
from integrations.mock_hospital.app import APPOINTMENTS, TASKS
from integrations.mock_hospital.app import app as hospital
from sqlalchemy import select

from app.main import app
from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from app.modules.interop.client import hospital_client
from app.modules.maternal.models import Device, Pregnancy
from app.modules.maternal.service import open_maternal_case
from app.modules.pathways.models import Evidence
from app.modules.patients.schemas import PatientCreate
from app.modules.patients.service import create_patient
from app.modules.tasks.models import NavigatorTask
from tests.test_state_machine import move


def _open(db, actor, name, sms=True):
    patient = create_patient(
        db, actor, PatientCreate(display_name=name, age_band="20-24", zone="Demo Zone Kisumu")
    )
    pregnancy = Pregnancy(
        patient_id=patient.id,
        gestation_band="28-36w",
        area_label="Demo Zone Kisumu",
        consent_care_coordination=True,
        consent_sms_reminders=sms,
        consent_band_contact=True,
        assigned_chw_id=actor.id,
        created_at=datetime(2026, 11, 20, 9, 0),
    )
    db.add(pregnancy)
    db.commit()
    case = open_maternal_case(db, patient, pregnancy, actor)
    return patient, pregnancy, case


def test_a_red_checkin_opens_one_task_and_the_audit_has_no_private_words(client, auth, db_session):
    chw = db_session.scalar(select(User).where(User.username == "chw"))
    _patient, pregnancy, case = _open(db_session, chw, "Mercy Desk")
    secret = "Mercy said she feels terrible in her own words"
    body = {
        "channel": "web",
        "language": "en",
        "answers": {"bleeding": "yes", "note": secret},
    }
    first = client.post(
        f"/api/v1/maternal/pregnancies/{pregnancy.id}/checkins",
        json=body,
        headers=auth["chw"],
    )
    assert first.status_code == 200, first.text
    assert first.json()["level"] == "red"
    second = client.post(
        f"/api/v1/maternal/pregnancies/{pregnancy.id}/checkins",
        json=body,
        headers=auth["nav"],
    )
    assert second.status_code == 200, second.text
    tasks = db_session.scalars(
        select(NavigatorTask).where(
            NavigatorTask.case_id == case.id,
            NavigatorTask.task_type == "maternal_warning",
            NavigatorTask.status == "open",
        )
    ).all()
    assert len(tasks) == 1
    assert tasks[0].priority == "urgent"
    logs = db_session.scalars(select(AuditLog).where(AuditLog.action == "checkin.recorded")).all()
    blob = " ".join(str(row.detail) for row in logs)
    assert secret not in blob
    assert "Mercy" not in blob


def test_sms_checkin_is_blocked_without_consent(client, auth, db_session):
    chw = db_session.scalar(select(User).where(User.username == "chw"))
    _patient, pregnancy, _case = _open(db_session, chw, "No Text", sms=False)
    response = client.post(
        f"/api/v1/maternal/pregnancies/{pregnancy.id}/checkins",
        json={"channel": "sms", "answers": {"bleeding": "yes"}},
        headers=auth["nav"],
    )
    assert response.status_code == 200, response.text
    assert response.json()["stored"] is False
    assert response.json()["task_id"] is None


def test_chw_cannot_approve_a_voucher_or_see_someone_else(client, auth, db_session):
    chw = db_session.scalar(select(User).where(User.username == "chw"))
    nav = db_session.scalar(select(User).where(User.username == "nav"))
    _patient, _pregnancy, case = _open(db_session, chw, "Fare Demo")
    other_patient, _other_preg, other = _open(db_session, nav, "Not Hers")
    denied = client.get(f"/api/v1/maternal/cases/{other.id}", headers=auth["chw"])
    assert denied.status_code == 403
    requested = client.post(
        f"/api/v1/maternal/cases/{case.id}/vouchers",
        json={"action": "request"},
        headers=auth["chw"],
    )
    assert requested.status_code == 200, requested.text
    assert requested.json()["provider"] == "SIMULATED_MPESA"
    assert requested.json()["amount_label"] == "assumed"
    blocked = client.post(
        f"/api/v1/maternal/cases/{case.id}/vouchers",
        json={"action": "approve"},
        headers=auth["chw"],
    )
    assert blocked.status_code == 403
    approved = client.post(
        f"/api/v1/maternal/cases/{case.id}/vouchers",
        json={"action": "approve"},
        headers=auth["nav"],
    )
    assert approved.status_code == 200
    cover = client.post(
        f"/api/v1/maternal/cases/{case.id}/cover",
        json={"status": "unknown"},
        headers=auth["nav"],
    )
    assert cover.json()["source"] == "SIMULATED_SHA"
    barrier = client.post(
        f"/api/v1/maternal/cases/{case.id}/barriers",
        json={"flag": "fare"},
        headers=auth["nav"],
    )
    assert barrier.status_code == 200
    assert other_patient.display_name == "Not Hers"


def test_summary_counts_a_red_journey(client, auth, db_session):
    chw = db_session.scalar(select(User).where(User.username == "chw"))
    _patient, pregnancy, case = _open(db_session, chw, "Red Count")
    assert move(client, auth["chw"], case.id, "home_screened").status_code == 200
    reading = client.post(
        f"/api/v1/maternal/pregnancies/{pregnancy.id}/readings",
        json={
            "systolic": 150,
            "diastolic": 96,
            "pulse": 80,
            "urine_protein": "neg",
            "hb_band": "normal",
            "danger_signs": ["headache_severe", "vision_blurred"],
        },
        headers=auth["chw"],
    )
    assert reading.status_code == 200, reading.text
    assert reading.json()["level"] == "red"
    summary = client.get("/api/v1/maternal/summary", headers=auth["nav"]).json()
    assert summary["red"] >= 1
    assert any(row["case_id"] == case.id for row in summary["red_cases"])
    assert summary["review"] == "PENDING CLINICAL REVIEW"


def test_antenatal_milestones_move_the_maternal_journey(client, auth, db_session):
    chw = db_session.scalar(select(User).where(User.username == "chw"))
    _patient, _pregnancy, case = _open(db_session, chw, "Clinic Demo")
    assert move(client, auth["chw"], case.id, "home_screened").status_code == 200
    assert move(client, auth["nav"], case.id, "navigating").status_code == 200
    APPOINTMENTS.clear()
    TASKS.clear()
    clinic = TestClient(hospital)

    def override():
        yield clinic

    app.dependency_overrides[hospital_client] = override
    try:
        requested = client.post(f"/api/v1/cases/{case.id}/hospital/request", headers=auth["nav"])
        assert requested.status_code == 200, requested.text
        assert client.get(f"/api/v1/cases/{case.id}", headers=auth["nav"]).json()["state"] == (
            "visit_booked"
        )
        expected = ("arrived", "arrived", "with_hospital")
        for state in expected:
            advanced = client.post(
                f"/api/v1/cases/{case.id}/hospital/advance", headers=auth["clin"]
            )
            assert advanced.status_code == 200, advanced.text
            assert (
                client.get(f"/api/v1/cases/{case.id}", headers=auth["clin"]).json()["state"]
                == state
            )
        assert advanced.json()["milestones"] == [
            "arrived",
            "antenatal_visit_completed",
            "care_plan_recorded",
        ]
    finally:
        app.dependency_overrides.pop(hospital_client, None)
        clinic.close()
    db_session.expire_all()
    evidence = db_session.scalars(select(Evidence).where(Evidence.case_id == case.id)).all()
    assert any(row.type == "facility_confirmation" for row in evidence)


def test_a_promoter_can_lend_only_her_own_band(client, auth, db_session):
    chw = db_session.scalar(select(User).where(User.username == "chw"))
    _patient, pregnancy, _case = _open(db_session, chw, "Band Demo")
    band = Device(
        kind="band",
        pseudonymous_device_id="BAND-TEST",
        api_key_hash="not-used",
        status="active",
        assigned_chw_id=chw.id,
    )
    db_session.add(band)
    db_session.commit()
    lent = client.post(
        f"/api/v1/maternal/pregnancies/{pregnancy.id}/band",
        json={"device_id": "BAND-TEST", "action": "lend"},
        headers=auth["chw"],
    )
    assert lent.status_code == 200, lent.text
    assert lent.json()["status"] == "lent"
    other = client.post(
        f"/api/v1/maternal/pregnancies/{pregnancy.id}/band",
        json={"device_id": "BAND-TEST", "action": "return"},
        headers=auth["nav"],
    )
    assert other.status_code == 200


@pytest.mark.parametrize("role", ["chw"])
def test_chw_summary_does_not_call_the_cervical_analytics_route(client, auth, role):
    response = client.get("/api/v1/analytics/summary", headers=auth[role])
    assert response.status_code == 403
