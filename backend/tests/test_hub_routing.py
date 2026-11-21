"""The Cuff hub on the patient account: readings reach her booklet, and the colour decides
how loudly a navigator hears about it (yellow a note, red urgent)."""

from sqlalchemy import select

from app.core import clock
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.followup.links import DEMO_CARD_ID, ensure_demo_patient
from app.modules.maternal.models import Device
from app.modules.tasks.models import NavigatorTask

from .conftest import PASSWORD_HASH, login

KEY = "synthetic-device-key"
CALM = {"systolic": 118, "diastolic": 76, "pulse": 72, "urine_protein": "neg", "hb_band": "normal"}


def _setup(client, db_session):
    db_session.add_all(
        [
            User(
                username="aisha",
                password_hash=PASSWORD_HASH,
                role="patient",
                display_name="Aisha Demo",
            ),
            User(
                username="david",
                password_hash=PASSWORD_HASH,
                role="clinician",
                display_name="David Kamau",
            ),
            Device(
                kind="hub",
                pseudonymous_device_id="HUB-0007",
                api_key_hash=hash_password(KEY),
                status="active",
                last_seen_at=clock.now(),
            ),
        ]
    )
    db_session.commit()
    ensure_demo_patient(db_session)
    return login(client, "aisha")


def _send(client, seq, ref, **reading):
    body = {
        "device_id": "HUB-0007",
        "client_reading_id": f"HUB-0007-{seq}",
        "pregnancy_ref": ref,
        "danger_signs": [],
        **CALM,
        **reading,
    }
    res = client.post("/api/v1/device/readings", json=body, headers={"X-Device-Key": KEY})
    assert res.status_code == 200, res.text
    return res.json()


def _warnings(db_session):
    return db_session.scalars(
        select(NavigatorTask).where(
            NavigatorTask.task_type == "maternal_warning", NavigatorTask.status == "open"
        )
    ).all()


def test_the_patient_sees_only_her_own_booklet(client, auth, db_session):
    aisha = _setup(client, db_session)
    mine = client.get("/api/v1/followup/my-booklet", headers=aisha)
    assert mine.status_code == 200, mine.text
    assert mine.json()["ref"] == DEMO_CARD_ID
    assert client.get("/api/v1/followup/my-booklet", headers=auth["nav"]).status_code == 403


def test_the_booklet_is_created_once(client, db_session):
    _setup(client, db_session)
    ensure_demo_patient(db_session)
    ensure_demo_patient(db_session)
    from app.modules.maternal.models import Pregnancy

    assert len(db_session.scalars(select(Pregnancy)).all()) == 1


def test_green_reading_opens_no_task(client, db_session):
    _setup(client, db_session)
    assert _send(client, 1, DEMO_CARD_ID)["level"] == "green"
    assert _warnings(db_session) == []


def test_yellow_is_a_normal_note_and_red_makes_it_urgent(client, auth, db_session):
    _setup(client, db_session)
    yellow = _send(client, 1, DEMO_CARD_ID, systolic=142, diastolic=92)
    assert yellow["level"] == "yellow"
    [task] = _warnings(db_session)
    assert task.priority == "normal"
    assert "yellow" in task.summary

    listed = client.get("/api/v1/navigator/tasks", headers=auth["nav"]).json()
    shown = next(row for row in listed if row["id"] == task.id)
    assert shown["patient_display_name"] == "Aisha Demo"
    assert shown["source"] == "device"

    red = _send(client, 2, DEMO_CARD_ID, danger_signs=["heavy_bleeding"])
    assert red["level"] == "red"
    [task] = _warnings(db_session)
    assert task.priority == "urgent"
    assert "red" in task.summary

    # a later yellow never softens an open red
    _send(client, 3, DEMO_CARD_ID, systolic=142, diastolic=92)
    [task] = _warnings(db_session)
    assert task.priority == "urgent"
    assert "red" in task.summary
