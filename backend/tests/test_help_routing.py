"""Help asked for on the patient side must reach staff with the person named.

Covers the paths that arrive without a card ID: the patient's support chat, USSD
and SMS. The card, sign-language and Telegram paths are covered in their own files.
"""

from sqlalchemy import select

from app.modules.auth.models import User
from app.modules.followup.links import DEMO_CARD_ID, DEMO_HANDSET, ensure_demo_patient
from app.modules.followup.models import Enrolment, PatientLink
from app.modules.tasks.models import NavigatorTask

from .conftest import PASSWORD_HASH, login


def _demo_patient(client, db_session):
    """The demo patient account and the clinician who issues her card, as the workspace seed has them."""
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
        ]
    )
    db_session.commit()
    ensure_demo_patient(db_session)
    enrolment = db_session.scalar(select(Enrolment).where(Enrolment.public_id == DEMO_CARD_ID))
    assert enrolment is not None
    return enrolment.case_id, login(client, "aisha")


def _open(db_session, task_type):
    return db_session.scalars(
        select(NavigatorTask).where(
            NavigatorTask.task_type == task_type, NavigatorTask.status == "open"
        )
    ).all()


def test_demo_patient_gets_one_card_and_it_is_idempotent(client, db_session):
    case_id, _ = _demo_patient(client, db_session)
    ensure_demo_patient(db_session)
    ensure_demo_patient(db_session)
    assert len(db_session.scalars(select(PatientLink)).all()) == 1
    assert (
        len(db_session.scalars(select(Enrolment).where(Enrolment.public_id == DEMO_CARD_ID)).all())
        == 1
    )
    assert case_id is not None


def test_support_chat_confirmed_worry_names_the_patient(client, auth, db_session):
    case_id, aisha = _demo_patient(client, db_session)
    first = client.post(
        "/api/v1/assistant/message",
        json={"channel": "web", "text": "I cannot afford the bus fare"},
        headers=aisha,
    )
    assert first.status_code == 200, first.text
    assert not _open(db_session, "navigator_followup"), (
        "a suggested worry stays private until confirmed"
    )
    confirmed = client.post(
        "/api/v1/assistant/message",
        json={"channel": "web", "confirm_flag": "transport_access"},
        headers=aisha,
    )
    assert confirmed.status_code == 200, confirmed.text
    [task] = _open(db_session, "navigator_followup")
    assert task.case_id == case_id

    listed = client.get("/api/v1/navigator/tasks", headers=auth["nav"]).json()
    shown = next(row for row in listed if row["id"] == task.id)
    assert shown["patient_display_name"] == "Aisha Demo"


def test_support_chat_cannot_raise_help_on_someone_elses_case(client, auth, db_session, make_case):
    own_case, aisha = _demo_patient(client, db_session)
    _patient, other = make_case()
    client.post(
        "/api/v1/assistant/message",
        json={"channel": "web", "text": "I want to talk to someone", "case_id": other["case_id"]},
        headers=aisha,
    )
    [task] = _open(db_session, "navigator_callback")
    assert task.case_id == own_case


def test_ussd_talk_now_names_the_handset_owner(client, db_session):
    case_id, _ = _demo_patient(client, db_session)
    client.post(
        "/api/v1/channels/ussd", json={"session_id": "s1", "phone_ref": DEMO_HANDSET, "text": ""}
    )
    res = client.post(
        "/api/v1/channels/ussd", json={"session_id": "s1", "phone_ref": DEMO_HANDSET, "text": "6"}
    )
    assert res.status_code == 200, res.text
    [task] = _open(db_session, "navigator_callback")
    assert task.case_id == case_id


def test_sms_help_matches_a_card_by_its_contact_number(client, auth, db_session):
    opened = client.post(
        "/api/v1/followup/register",
        json={
            "age_band": "30-34",
            "area_label": "Demo Zone A",
            "screening_type": "general",
            "finding": "concerning",
            "consent": True,
            "contact": "0700000555",
        },
        headers=auth["clin"],
    ).json()
    # the gateway sends the international form; the card was issued with the local one
    res = client.post(
        "/api/v1/channels/sms/inbound", json={"phone_ref": "+254700000555", "text": "3"}
    )
    assert res.status_code == 200, res.text
    [task] = _open(db_session, "navigator_callback")
    assert task.case_id == opened["case_id"]


def test_sms_from_an_unknown_number_still_opens_a_task(client, db_session):
    res = client.post(
        "/api/v1/channels/sms/inbound", json={"phone_ref": "+254799999999", "text": "3"}
    )
    assert res.status_code == 200, res.text
    [task] = _open(db_session, "navigator_callback")
    assert task.case_id is None
