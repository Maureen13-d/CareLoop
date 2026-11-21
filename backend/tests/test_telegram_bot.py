"""Telegram bot: secret, binding, menus, check-ins, and the demo transcript."""

import json

from sqlalchemy import select

from app.core import clock
from app.core.db import Base
from app.modules.audit.models import AuditLog
from app.modules.followup.discreet import problems
from app.modules.followup.models import Enrolment
from app.modules.followup.telegram_copy import all_strings
from app.modules.followup.telegram_flow import mint_link
from app.modules.followup.telegram_models import TelegramDeepLink, TelegramVault
from app.modules.ksl.models import KslFacilityFlag
from app.modules.pathways.models import CareCase
from app.modules.tasks.models import NavigatorTask
from tests.test_followup_loop import enrol

SECRET = {"X-Telegram-Bot-Api-Secret-Token": "test-secret"}


def _redact(text: str) -> str:
    import re

    return re.sub(r"SIMULATED code: \d+", "SIMULATED code: CODE", text)


def _post(client, chat, update_id, text="", callback=None, media=None, chat_type="private"):
    body = {
        "chat_id": chat,
        "text": text,
        "update_id": str(update_id),
        "chat_type": chat_type,
        "message_id": update_id,
    }
    if callback:
        body["callback"] = callback
    if media:
        body["media"] = media
    res = client.post("/api/v1/followup/telegram/simulate", json=body)
    assert res.status_code == 200, res.text
    return res.json()


def _bind(client, auth, chat="tg-chat-991122"):
    import os

    os.environ["CARELOOP_EXPOSE_SIMULATED_CODES"] = "true"
    opened = enrol(client, auth, channel="telegram")
    assert "English" in _post(client, chat, 1, "/start")["reply_text"]
    assert "encrypted" in _post(client, chat, 2, "1")["reply_text"].lower()
    assert "card" in _post(client, chat, 3, "OK")["reply_text"].lower()
    asked = _post(client, chat, 4, opened["public_id"])["reply_text"]
    code = asked.split("SIMULATED code:", 1)[1].strip().split()[0]
    done = _post(client, chat, 5, code)
    assert "menu" in done["reply_text"].lower()
    return opened, chat


def test_secret_and_duplicate_update(client):
    import os

    os.environ["CARELOOP_TELEGRAM_WEBHOOK_SECRET"] = "test-secret"
    missing = client.post(
        "/api/v1/followup/telegram/webhook",
        json={"chat_id": "a", "text": "hi", "update_id": "d1"},
    )
    assert missing.status_code == 401
    bad = client.post(
        "/api/v1/followup/telegram/webhook",
        json={"chat_id": "a", "text": "hi", "update_id": "d1"},
        headers={"X-Telegram-Bot-Api-Secret-Token": "nope"},
    )
    assert bad.status_code == 401
    ok = client.post(
        "/api/v1/followup/telegram/webhook",
        json={"chat_id": "a", "text": "/start", "update_id": "d1"},
        headers=SECRET,
    )
    assert ok.status_code == 200, ok.text
    again = client.post(
        "/api/v1/followup/telegram/webhook",
        json={"chat_id": "a", "text": "/start", "update_id": "d1"},
        headers=SECRET,
    )
    assert again.json()["duplicate"] is True


def test_deep_link_is_single_use_and_not_the_patient_id(client, auth, db_session):
    opened = enrol(client, auth, channel="telegram")
    token = mint_link(db_session, opened["public_id"])
    db_session.commit()
    assert token != opened["public_id"]
    assert opened["public_id"] not in token
    chat = "tg-chat-link"
    first = _post(client, chat, 1, f"/start {token}")
    assert "English" in first["reply_text"]
    row = db_session.scalar(select(TelegramDeepLink).where(TelegramDeepLink.token == token))
    row.expires_at = clock.now().replace(year=clock.now().year - 1)
    db_session.commit()
    expired = _post(client, "tg-chat-expired", 1, f"/start {token}")
    assert "not accepted" in expired["reply_text"].lower()
    fresh = mint_link(db_session, opened["public_id"])
    db_session.commit()
    _post(client, "tg-chat-once", 1, f"/start {fresh}")
    _post(client, "tg-chat-once", 2, "1")
    _post(client, "tg-chat-once", 3, "OK")
    asked = _post(client, "tg-chat-once", 4, opened["public_id"])["reply_text"]
    code = asked.split("SIMULATED code:", 1)[1].strip().split()[0]
    _post(client, "tg-chat-once", 5, code)
    used = db_session.scalar(select(TelegramDeepLink).where(TelegramDeepLink.token == fresh))
    db_session.refresh(used)
    assert used.used_at is not None
    second = _post(client, "tg-chat-twice", 1, f"/start {fresh}")
    assert "not accepted" in second["reply_text"].lower()


def test_unknown_and_wrong_ids_match_and_lock(client, auth):
    enrol(client, auth, channel="telegram")
    chat = "tg-chat-lock"
    _post(client, chat, 1, "1")
    _post(client, chat, 2, "OK")
    unknown = _post(client, chat, 3, "AAAA-AAAA-AAAA-A")["reply_text"]
    wrong = _post(client, chat, 4, "not-an-id")["reply_text"]
    assert unknown == wrong
    for index in range(5, 9):
        _post(client, chat, index, "still-wrong")
    locked = _post(client, chat, 9, "still-wrong")["reply_text"]
    assert locked == unknown


def test_chat_id_stays_in_the_telegram_vault(client, auth, db_session):
    opened, chat = _bind(client, auth, "tg-chat-991122")
    vault = db_session.scalar(select(TelegramVault).where(TelegramVault.public_id == opened["public_id"]))
    db_session.refresh(vault)
    assert vault.chat_id == chat
    for table in Base.metadata.sorted_tables:
        if table.name == "telegram_vault":
            continue
        rows = db_session.execute(table.select()).all()
        assert chat not in json.dumps(rows, default=str)


def test_callback_data_has_no_patient_id(client, auth):
    opened, chat = _bind(client, auth, "tg-chat-buttons")
    shown = _post(client, chat, 6, "💬 I need help")
    blob = json.dumps(shown["buttons"])
    assert opened["public_id"] not in blob
    assert all(len(button["id"].encode()) <= 64 for button in shown["buttons"])


def test_worse_and_not_sure_open_one_urgent_task_without_reassurance(client, auth, db_session):
    _opened, chat = _bind(client, auth)
    worse = _post(client, chat, 6, "Worse")["reply_text"]
    assert "please go to the nearest clinic now" in worse.lower()
    assert "you are fine" not in worse.lower()
    assert "🎉" not in worse
    tasks = list(
        db_session.scalars(select(NavigatorTask).where(NavigatorTask.task_type == "followup_urgent"))
    )
    assert len(tasks) == 1
    other, other_chat = _bind(client, auth, "tg-chat-unsure")
    unsure = _post(client, other_chat, 6, "Not sure")["reply_text"]
    assert "please go to the nearest clinic now" in unsure.lower()
    assert "🎉" not in unsure
    count = list(
        db_session.scalars(
            select(NavigatorTask).where(
                NavigatorTask.task_type == "followup_urgent",
                NavigatorTask.case_id == other["case_id"],
            )
        )
    )
    assert len(count) == 1


def test_same_and_better_still_send_the_person_to_clinic(client, auth):
    _opened, chat = _bind(client, auth, "tg-chat-same")
    same = _post(client, chat, 6, "Same")["reply_text"].lower()
    assert "please still go to your clinic" in same
    better = _post(client, chat, 7, "Better")["reply_text"].lower()
    assert "please still go to your clinic" in better


def test_saying_i_went_does_not_close_the_case(client, auth, db_session):
    opened, chat = _bind(client, auth, "tg-chat-went")
    reply = _post(client, chat, 6, "I went")["reply_text"].lower()
    assert "confirm" in reply
    case = db_session.get(CareCase, opened["case_id"])
    db_session.refresh(case)
    assert case.state != "arrived"
    row = db_session.scalar(select(Enrolment).where(Enrolment.public_id == opened["public_id"]))
    assert row.reported_visit is True


def test_stop_unbinds_and_start_asks_again(client, auth, db_session):
    opened, chat = _bind(client, auth, "tg-chat-stop")
    stopped = _post(client, chat, 6, "STOP")["reply_text"].lower()
    assert "stopped" in stopped
    vault = db_session.scalar(select(TelegramVault).where(TelegramVault.public_id == opened["public_id"]))
    db_session.refresh(vault)
    assert vault.chat_id is None
    again = _post(client, chat, 7, "START")["reply_text"].lower()
    assert "card" in again
    assert "stay off" in again


def test_blocked_bot_marks_unreachable_once(client, auth, db_session, monkeypatch):
    opened, chat = _bind(client, auth, "tg-chat-block")

    def blocked(method, payload):
        return {"ok": False, "error_code": 403, "description": "Forbidden: bot was blocked by the user"}

    monkeypatch.setattr("app.modules.followup.telegram.post_json", blocked)
    from app.modules.followup.telegram import deliver

    deliver(db_session, chat, {"messages": [{"text": "Hi"}], "duplicate": False})
    db_session.commit()
    vault = db_session.scalar(select(TelegramVault).where(TelegramVault.public_id == opened["public_id"]))
    db_session.refresh(vault)
    assert vault.unreachable is True
    deliver(db_session, chat, {"messages": [{"text": "Hi again"}], "duplicate": False})
    tasks = list(
        db_session.scalars(
            select(NavigatorTask).where(NavigatorTask.task_type == "followup_unreachable")
        )
    )
    assert len(tasks) == 1
    assert "another channel" in tasks[0].title.lower()


def test_quiet_hours_and_caps(client, auth, db_session):
    from datetime import datetime

    from app.modules.followup.checkins import run_checkins

    opened = enrol(client, auth, channel="telegram")
    night = datetime(2026, 11, 20, 22, 0)
    assert run_checkins(db_session, night) == 0
    row = db_session.scalar(select(Enrolment).where(Enrolment.public_id == opened["public_id"]))
    row.checkin_attempts = 6
    db_session.commit()
    morning = datetime(2026, 11, 20, 10, 0)
    assert run_checkins(db_session, morning) == 0


def test_telegram_strings_are_discreet_and_urgent_lines_are_plain():
    urgent = {"worse", "unsure", "danger"}
    for language, key, text in all_strings():
        assert problems(text) == [], (language, key, problems(text))
        if key in urgent:
            assert "🎉" not in text
            assert "👋" not in text


def test_a_diagnosis_question_names_the_person_and_the_demo_clinic(client, auth, monkeypatch):
    monkeypatch.setenv("CARELOOP_LLM_API_KEY", "")
    _bind(client, auth, "tg-diagnosis-person")
    reply = _post(client, "tg-diagnosis-person", 6, "But what if the diagnosis is wrong")["reply_text"]
    assert "Chw" in reply
    assert "Market clinic" in reply
    assert "8 to 4" in reply
    assert "you are fine" not in reply.lower()
    again = _post(client, "tg-diagnosis-person", 7, "The diagnosis is whack")["reply_text"]
    assert again == reply


def test_a_diagnosis_question_names_the_clinic_when_the_area_has_one(client, auth, monkeypatch):
    import os

    monkeypatch.setenv("CARELOOP_LLM_API_KEY", "")
    os.environ["CARELOOP_EXPOSE_SIMULATED_CODES"] = "true"
    opened = enrol(client, auth, channel="telegram", area_label="East")
    chat = "tg-diagnosis-east"
    _post(client, chat, 1, "/start")
    _post(client, chat, 2, "1")
    _post(client, chat, 3, "OK")
    asked = _post(client, chat, 4, opened["public_id"])["reply_text"]
    code = asked.split("SIMULATED code:", 1)[1].strip().split()[0]
    _post(client, chat, 5, code)
    reply = _post(client, chat, 6, "But what if the diagnosis is wrong")["reply_text"]
    assert "Chw" in reply
    assert "Hill clinic" in reply
    assert "8 to 12" in reply


def test_the_model_can_choose_the_ask_line(client, auth, monkeypatch):
    from app.modules.followup import telegram_phrase as phrase

    monkeypatch.setenv("CARELOOP_LLM_API_KEY", "test-key")

    def completer(system, user):
        if system.startswith("Choose"):
            return "ask_person"
        return "You are fine. Go to Kenyatta."

    phrase.set_complete(completer)
    try:
        _bind(client, auth, "tg-diagnosis-route")
        reply = _post(client, "tg-diagnosis-route", 6, "what if they got it wrong")["reply_text"]
    finally:
        phrase.set_complete(None)
    assert "Chw" in reply
    assert "Kenyatta" not in reply
    assert "you are fine" not in reply.lower()


def test_a_stopped_chat_can_enter_the_new_code(client, auth, db_session):
    opened, chat = _bind(client, auth, "tg-chat-restart")
    stopped = _post(client, chat, 6, "/stop")
    assert stopped["reply_text"] == "Messages stopped."
    restart = _post(client, chat, 7, "/start")
    assert "card" in restart["reply_text"].lower()
    asked = _post(client, chat, 8, opened["public_id"])["reply_text"]
    code = asked.split("SIMULATED code:", 1)[1].strip().split()[0]
    done = _post(client, chat, 9, code)
    assert "messages stopped" not in done["reply_text"].lower()
    assert "menu" in done["reply_text"].lower()
    row = db_session.scalar(select(Enrolment).where(Enrolment.public_id == opened["public_id"]))
    db_session.refresh(row)
    assert row.messages_stopped is False


def test_group_and_non_text_do_not_error(client):
    first = _post(client, "tg-group", 1, "hello", chat_type="group")
    assert "private" in first["reply_text"].lower()
    second = _post(client, "tg-group", 2, "hello again", chat_type="group")
    assert second["reply_text"] == ""
    voice = _post(client, "tg-voice", 1, media="voice")
    assert "voice" in voice["reply_text"].lower()
    place = _post(client, "tg-voice", 2, media="location")
    assert "do not store" in place["reply_text"].lower()


def test_golden_transcript_matches_on_both_doors(client, auth):
    import os

    os.environ["CARELOOP_TELEGRAM_WEBHOOK_SECRET"] = "test-secret"
    os.environ["CARELOOP_EXPOSE_SIMULATED_CODES"] = "true"
    opened = enrol(client, auth, channel="telegram")

    def script(door, chat):
        lines = []

        def say(update_id, text="", callback=None):
            body = {"chat_id": chat, "text": text, "update_id": f"{door}-{update_id}", "message_id": update_id}
            if callback:
                body["callback"] = callback
            if door == "hook":
                res = client.post("/api/v1/followup/telegram/webhook", json=body, headers=SECRET)
            else:
                res = client.post("/api/v1/followup/telegram/simulate", json=body)
            assert res.status_code == 200, res.text
            payload = res.json()
            lines.append(payload["reply_text"])
            return payload["reply_text"]

        say(1, "/start")
        say(2, "1")
        say(3, "OK")
        asked = say(4, opened["public_id"])
        code = asked.split("SIMULATED code:", 1)[1].strip().split()[0]
        say(5, code)
        say(6, "Not yet")
        say(7, callback="bar:transport")
        say(8, callback="bar:done")
        say(9, "Worse")
        return lines

    simulated = [ _redact(line) for line in script("sim", "tg-demo-sim") ]
    hooked = [ _redact(line) for line in script("hook", "tg-demo-hook") ]
    assert simulated == hooked
    assert "not a person or a doctor" in simulated[0].lower()
    assert "a person will help" in simulated[7].lower()
    assert "nearest clinic now" in simulated[8].lower()
    assert "🎉" not in simulated[8]


def test_help_interpreter_sets_the_facility_flag(client, auth, db_session):
    _opened, chat = _bind(client, auth, "tg-chat-sign")
    _post(client, chat, 6, callback="help:sign")
    flag = db_session.scalar(select(KslFacilityFlag))
    assert flag is not None and flag.interpreter_available is True


def test_audit_does_not_store_the_typed_id(client, auth, db_session):
    opened, chat = _bind(client, auth, "tg-chat-audit")
    blob = json.dumps(
        [row.detail for row in db_session.scalars(select(AuditLog)).all()],
        default=str,
    )
    assert opened["public_id"] not in blob
    assert chat not in blob
