"""KSL follow-up: captions, no phone-call default, guided taps, and one human task."""

from types import SimpleNamespace

from sqlalchemy import select

from app.core import clock
from app.modules.followup.checkins import run_checkins
from app.modules.followup.conversation import get_session, handle, respond
from app.modules.followup.models import Enrolment
from app.modules.followup.texts import line
from app.modules.followup.worklist import action_for
from app.modules.ksl.fallback import choose, step_after
from app.modules.ksl.guided import DisabledRecognizer, GuidedCall, SimulatorRecognizer
from app.modules.ksl.router import reset_calls
from app.modules.tasks.models import NavigatorTask

PASSWORD = "test-password"


def enrol(client, auth):
    resp = client.post(
        "/api/v1/followup/register",
        json={
            "age_band": "30-34",
            "area_label": "Demo Zone A",
            "screening_type": "general",
            "finding": "concerning",
            "consent": True,
            "language": "en",
            "channel": "web",
            "contact": "0700000888",
            "assigned_chw_username": "chw",
        },
        headers=auth["clin"],
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _token(client, auth, public_id):
    client.post("/api/v1/followup/access/start", json={"public_id": public_id, "client_key": "ksl"})
    code = client.get(
        "/api/v1/followup/access/dev-code",
        params={"public_id": public_id},
        headers=auth["clin"],
    ).json()["simulated_code"]
    checked = client.post(
        "/api/v1/followup/access/check",
        json={"public_id": public_id, "code": code, "client_key": "ksl"},
    )
    assert checked.status_code == 200, checked.text
    return {"Authorization": f"Bearer {checked.json()['access_token']}"}


def _awake():
    while clock.now().hour >= 21 or clock.now().hour < 7:
        clock.advance(1)


def test_core_reply_carries_the_template_and_does_not_reassure(client, auth, db_session):
    enrolled = enrol(client, auth)
    row = db_session.scalar(select(Enrolment).where(Enrolment.public_id == enrolled["public_id"]))
    result = respond(db_session, row, "web", "ksl", "worse")
    assert result["template_id"] == "worse"
    assert result["ksl"]["caption"] == line("worse", "en")
    assert "you are fine" not in result["reply_text"].lower()
    assert "nothing to worry" not in result["reply_text"].lower()
    assert row.language == "ksl"

    session = get_session(db_session, "ussd", "ksl-open")
    opened = handle(db_session, session, "3")
    assert session.language == "ksl"
    assert opened["template_id"] == "ask_id"
    assert opened["ksl"]["channel_limit"] == "text_only"
    assert opened["ksl"]["available"] is False


def test_telegram_without_a_video_asks_a_person(client, auth, db_session):
    enrolled = enrol(client, auth)
    row = db_session.scalar(select(Enrolment).where(Enrolment.public_id == enrolled["public_id"]))
    result = respond(db_session, row, "telegram", "ksl", "hello there")
    assert result["ksl"]["available"] is False
    assert result["ksl"]["icons"]
    tasks = db_session.scalars(
        select(NavigatorTask).where(
            NavigatorTask.case_id == row.case_id,
            NavigatorTask.task_type == "followup_ksl",
        )
    ).all()
    assert len(tasks) == 1


def test_ksl_checkin_and_worklist_do_not_wait_on_a_phone_call(client, auth, db_session):
    first = enrol(client, auth)
    second = enrol(client, auth)
    ksl_row = db_session.scalar(select(Enrolment).where(Enrolment.public_id == first["public_id"]))
    en_row = db_session.scalar(select(Enrolment).where(Enrolment.public_id == second["public_id"]))
    ksl_row.language = "ksl"
    db_session.commit()
    _awake()
    assert run_checkins(db_session) >= 1
    ksl_tasks = db_session.scalars(
        select(NavigatorTask).where(
            NavigatorTask.case_id == ksl_row.case_id,
            NavigatorTask.task_type == "followup_unreached",
        )
    ).all()
    en_tasks = db_session.scalars(
        select(NavigatorTask).where(
            NavigatorTask.case_id == en_row.case_id,
            NavigatorTask.task_type == "followup_unreached",
        )
    ).all()
    assert len(ksl_tasks) == 1
    assert en_tasks == []
    assert action_for(SimpleNamespace(language="ksl", symptom_flag="none", barrier_label=None)) == "text or video"
    assert (
        action_for(SimpleNamespace(language="ksl", symptom_flag="none", barrier_label="interpreter"))
        == "book interpreter"
    )
    assert action_for(SimpleNamespace(language="en", symptom_flag="none", barrier_label=None)) == "call"
    flag = client.post(
        "/api/v1/ksl/facilities/demo-clinic/interpreter",
        json={"interpreter_available": True, "recorded_on": "2026-11-21"},
        headers=auth["clin"],
    )
    assert flag.status_code == 200, flag.text
    assert flag.json()["recorded_on"] == "2026-11-21"


def test_guided_call_confirms_before_one_task(client, auth):
    reset_calls()
    enrolled = enrol(client, auth)
    headers = _token(client, auth, enrolled["public_id"])
    refused = client.post(
        "/api/v1/ksl/guided",
        json={"action": "tap", "choice": "worse", "video": "raw-bytes"},
        headers=headers,
    )
    assert refused.status_code == 422

    tapped = client.post(
        "/api/v1/ksl/guided",
        json={"action": "tap", "choice": "worse"},
        headers=headers,
    )
    assert tapped.status_code == 200, tapped.text
    assert tapped.json()["phase"] == "confirm"
    assert tapped.json()["tasks_opened"] == 0
    assert tapped.json()["recognition"] == "Recognition not enabled in this build."

    done = client.post(
        "/api/v1/ksl/guided",
        json={"action": "confirm", "yes": True},
        headers=headers,
    )
    assert done.status_code == 200, done.text
    assert done.json()["tasks"] == ["worse"]
    assert done.json()["tasks_opened"] == 1
    assert "you are fine" not in (done.json()["reply_text"] or "").lower()


def test_recogniser_is_a_simulator_and_the_ladder_is_ordered():
    call = GuidedCall()
    missed = call.recognize(SimulatorRecognizer(), "worse", 0.2)
    assert missed["phase"] == "ask"
    heard = call.recognize(SimulatorRecognizer(), "worse", 0.95)
    assert heard["phase"] == "confirm"
    assert heard["committed"] is None
    blocked = GuidedCall().recognize(DisabledRecognizer(), "worse", 1)
    assert blocked["committed"] is None
    assert blocked["recognition"] == "Recognition not enabled in this build."
    assert choose(False, True, True) == "video"
    assert choose(False, False, True) == "captions"
    assert choose(False, False, False) == "human"
    assert step_after("avatar") == "video"
    assert step_after("human") == "human"
