"""Maternal pathway: reachable states, role limits, and the CHW's own list."""

from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.errors import DomainError
from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from app.modules.maternal.models import Device, Pregnancy, Reading
from app.modules.maternal.service import open_maternal_case
from app.modules.pathways.loader import load_pathway
from app.modules.pathways.models import CareCase
from app.modules.pathways.service import transition
from app.modules.patients.schemas import PatientCreate
from app.modules.patients.service import create_patient
from tests.test_state_machine import move


def test_every_state_is_reachable_and_endings_are_not_edges():
    pw = load_pathway("maternal")
    seen: set[str] = set()
    stack = [pw.initial_state]
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        stack.extend(pw.states[name].next)
    assert seen == set(pw.states)
    assert {name for name, state in pw.states.items() if "chw" in state.roles} == {
        "enrolled",
        "home_screened",
    }
    assert "navigator" not in pw.states["arrived"].roles
    assert pw.states["risk_flagged"].urgent_deadline_hours == 2
    assert pw.closed_state == "closed"
    assert pw.declined_state == "chose_to_stop"
    assert pw.lost_state == "closed_by_person"
    for state in pw.states.values():
        assert state.roles
        for target in state.next:
            assert target not in pw.terminal_states

    cervical = load_pathway()
    assert cervical.closed_state == "CLOSED"
    assert cervical.declined_state == "PATIENT_DECLINED"
    assert cervical.lost_state == "LOST_TO_FOLLOW_UP"


def _pregnancy(db, actor, name, chw_id):
    patient = create_patient(
        db, actor, PatientCreate(display_name=name, age_band="20-24", zone="Demo Zone Kisumu")
    )
    pregnancy = Pregnancy(
        patient_id=patient.id,
        gestation_band="28-36w",
        area_label="Demo Zone Kisumu",
        consent_care_coordination=True,
        consent_sms_reminders=False,
        consent_band_contact=False,
        assigned_chw_id=chw_id,
        created_at=datetime(2026, 11, 20, 9, 0),
    )
    db.add(pregnancy)
    db.commit()
    return patient, pregnancy


def test_chw_can_record_a_home_screen_but_not_book_or_confirm_arrival(client, auth, db_session):
    chw = db_session.scalar(select(User).where(User.username == "chw"))
    david = db_session.scalar(select(User).where(User.username == "clin"))
    patient, pregnancy = _pregnancy(db_session, chw, "Mercy Demo", chw.id)
    case = open_maternal_case(db_session, patient, pregnancy, chw)
    cid = case.id

    assert move(client, auth["chw"], cid, "home_screened").status_code == 200
    assert move(client, auth["chw"], cid, "navigating").status_code == 403
    assert move(client, auth["nav"], cid, "navigating").status_code == 200
    assert move(client, auth["nav"], cid, "visit_booked").status_code == 200
    denied = move(client, auth["nav"], cid, "arrived")
    assert denied.status_code == 403
    arrived = move(client, auth["clin"], cid, "arrived")
    assert arrived.status_code == 200
    assert david.role == "clinician"


def test_urgent_warning_uses_the_shorter_assumed_deadline(client, auth, db_session):
    chw = db_session.scalar(select(User).where(User.username == "chw"))
    patient, pregnancy = _pregnancy(db_session, chw, "Demo Adhiambo", chw.id)
    case = open_maternal_case(db_session, patient, pregnancy, chw)
    assert move(client, auth["chw"], case.id, "home_screened").status_code == 200
    case.urgency = "urgent"
    db_session.commit()
    moved = transition(db_session, case, "risk_flagged", None, "Synthetic warning")
    waited = moved.deadline_at - moved.state_entered_at
    assert waited.total_seconds() == 2 * 3600
    assert moved.urgency == "urgent"


def test_routine_warning_keeps_the_longer_assumed_deadline(client, auth, db_session):
    chw = db_session.scalar(select(User).where(User.username == "chw"))
    patient, pregnancy = _pregnancy(db_session, chw, "Demo Awuor", chw.id)
    case = open_maternal_case(db_session, patient, pregnancy, chw)
    assert move(client, auth["chw"], case.id, "home_screened").status_code == 200
    moved = transition(db_session, case, "risk_flagged", None)
    waited = moved.deadline_at - moved.state_entered_at
    assert waited.total_seconds() == 24 * 3600


def test_decline_keeps_her_words_on_the_case_and_out_of_the_audit(client, auth, db_session):
    chw = db_session.scalar(select(User).where(User.username == "chw"))
    patient, pregnancy = _pregnancy(db_session, chw, "Demo Nafula", chw.id)
    case = open_maternal_case(db_session, patient, pregnancy, chw)
    phrase = "she asked to stop in her own words"
    resp = client.post(
        f"/api/v1/cases/{case.id}/decline",
        json={"note": phrase},
        headers=auth["nav"],
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["state"] == "chose_to_stop"
    logs = db_session.scalars(select(AuditLog).where(AuditLog.action == "case.decline")).all()
    assert logs
    assert all(phrase not in str(entry.detail) for entry in logs)


def test_cervical_desk_does_not_list_maternal_journeys(client, auth, db_session):
    chw = db_session.scalar(select(User).where(User.username == "chw"))
    patient, pregnancy = _pregnancy(db_session, chw, "Demo Kerubo", chw.id)
    case = open_maternal_case(db_session, patient, pregnancy, chw)
    listed = client.get("/api/v1/cases?status=open", headers=auth["nav"]).json()
    assert case.id not in {row["id"] for row in listed}


def test_chw_list_is_limited_to_her_women(client, auth, db_session):
    chw = db_session.scalar(select(User).where(User.username == "chw"))
    nav = db_session.scalar(select(User).where(User.username == "nav"))
    _pregnancy(db_session, chw, "Mine Demo", chw.id)
    _pregnancy(db_session, nav, "Other Demo", nav.id)
    mine = client.get("/api/v1/maternal/pregnancies", headers=auth["chw"])
    assert mine.status_code == 200, mine.text
    assert [row["display_name"] for row in mine.json()] == ["Mine Demo"]
    everyone = client.get("/api/v1/maternal/pregnancies", headers=auth["nav"])
    assert {row["display_name"] for row in everyone.json()} == {"Mine Demo", "Other Demo"}
    assert client.get("/api/v1/maternal/pregnancies", headers=auth["counsellor"]).status_code == 403


def test_a_reading_id_is_unique_per_device(db_session):
    chw = db_session.scalar(select(User).where(User.username == "chw"))
    _, pregnancy = _pregnancy(db_session, chw, "Demo Chemutai", chw.id)
    device = Device(
        kind="hub",
        pseudonymous_device_id="HUB-TEST",
        api_key_hash="not-a-secret",
        assigned_chw_id=chw.id,
        status="active",
    )
    db_session.add(device)
    db_session.flush()
    now = datetime(2026, 11, 20, 9, 0)
    fields = {
        "pregnancy_id": pregnancy.id,
        "device_id": device.id,
        "client_reading_id": "HUB-TEST-1",
        "urine_protein": "unknown",
        "hb_band": "unknown",
        "danger_signs": [],
        "risk_level": "yellow",
        "rule_ids": ["INCOMPLETE_DATA"],
        "rules_version": "0.1-pending-clinical-review",
        "source": "hub",
        "taken_at": now,
        "received_at": now,
    }
    db_session.add(Reading(**fields))
    db_session.commit()
    db_session.add(Reading(**fields))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_opening_without_consent_is_refused(db_session):
    chw = db_session.scalar(select(User).where(User.username == "chw"))
    patient, pregnancy = _pregnancy(db_session, chw, "Demo No Consent", chw.id)
    pregnancy.consent_care_coordination = False
    db_session.commit()
    with pytest.raises(DomainError) as caught:
        open_maternal_case(db_session, patient, pregnancy, chw)
    assert caught.value.code == "consent_required"
    assert db_session.scalar(select(CareCase.id)) is None
