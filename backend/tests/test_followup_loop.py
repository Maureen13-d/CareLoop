"""Follow-up loop: ID, second check, worklist, safety, check-ins, Telegram."""

import json
import os
from datetime import datetime, timedelta

from sqlalchemy import func, select

from app.core import clock
from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from app.modules.followup.access import reset_limits
from app.modules.followup.checkins import run_checkins
from app.modules.followup.cohort import build_cohort, report
from app.modules.followup.conversation import guide_speaks
from app.modules.followup.discreet import problems
from app.modules.followup.evaluate import score_held_out
from app.modules.followup.ids import parse_public_id
from app.modules.followup.models import ContactVault, Enrolment, Outbound
from app.modules.followup.texts import templates
from app.modules.pathways.models import CareCase
from app.modules.pathways.service import run_deadline_check
from app.modules.tasks.models import NavigatorTask

PHONE = "0700000999"
ACTIONS = {"call", "home visit", "transport support", "counsellor", "escalate to clinician"}


def enrol(client, auth, **overrides):
    body = {
        "age_band": "30-34",
        "area_label": "Demo Zone A",
        "screening_type": "general",
        "finding": "concerning",
        "consent": True,
        "language": "en",
        "channel": "sms",
        "contact": PHONE,
        "assigned_chw_username": "chw",
    }
    body.update(overrides)
    resp = client.post("/api/v1/followup/register", json=body, headers=auth["clin"])
    assert resp.status_code == 201, resp.text
    return resp.json()


def _code(client, auth, public_id):
    resp = client.get(
        "/api/v1/followup/access/dev-code",
        params={"public_id": public_id},
        headers=auth["clin"],
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["simulated_code"]


def unlock(client, auth, public_id, client_key="device-a"):
    start = client.post(
        "/api/v1/followup/access/start",
        json={"public_id": public_id, "client_key": client_key},
    )
    assert start.status_code == 200, start.text
    token = client.post(
        "/api/v1/followup/access/check",
        json={
            "public_id": public_id,
            "code": _code(client, auth, public_id),
            "client_key": client_key,
        },
    )
    assert token.status_code == 200, token.text
    return {"Authorization": f"Bearer {token.json()['access_token']}"}


def test_register_issues_a_checked_id_and_hides_the_contact(client, auth):
    opened = enrol(client, auth, screening_type="hiv", language="sw")
    public_id = opened["public_id"]
    assert parse_public_id(public_id) == public_id
    assert parse_public_id(public_id[:-1] + "A") is None
    assert opened["status"] == "opened"
    assert len(opened["slip"]) == 3
    blob = json.dumps(opened)
    assert PHONE not in blob
    assert "hiv" not in blob
    slip = client.get(f"/api/v1/followup/slip/{public_id}", headers=auth["clin"])
    assert slip.status_code == 200, slip.text
    slip_blob = json.dumps(slip.json())
    assert PHONE not in slip_blob
    assert "hiv" not in slip_blob
    assert public_id in slip_blob
    assert "<svg" in (slip.json()["qr_svg"] or "")
    refused = enrol(client, auth, consent=False)
    assert refused["public_id"] is None
    skipped = enrol(client, auth, finding="not_concerning")
    assert skipped["public_id"] is None


def test_access_hides_unknown_ids_and_locks_out(client, auth):
    opened = enrol(client, auth)
    public_id = opened["public_id"]
    known = client.post(
        "/api/v1/followup/access/start", json={"public_id": public_id, "client_key": "k"}
    )
    unknown = client.post(
        "/api/v1/followup/access/start",
        json={"public_id": "AAAA-BBBB-CCCC-D", "client_key": "k"},
    )
    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json()
    wrong = client.post(
        "/api/v1/followup/access/check",
        json={"public_id": public_id, "code": "000000", "client_key": "k"},
    )
    missing = client.post(
        "/api/v1/followup/access/check",
        json={"public_id": "ZZZZ-ZZZZ-ZZZZ-Z", "code": "000000", "client_key": "k"},
    )
    assert wrong.status_code == missing.status_code == 401
    assert wrong.json() == missing.json()
    assert "state" not in wrong.json()
    me = client.get("/api/v1/followup/me")
    assert me.status_code == 401
    assert public_id not in me.text

    reset_limits()
    client.post(
        "/api/v1/followup/access/start", json={"public_id": public_id, "client_key": "lock"}
    )
    right = _code(client, auth, public_id)
    for _ in range(5):
        client.post(
            "/api/v1/followup/access/check",
            json={"public_id": public_id, "code": "111111", "client_key": "lock"},
        )
    locked = client.post(
        "/api/v1/followup/access/check",
        json={"public_id": public_id, "code": right, "client_key": "lock"},
    )
    assert locked.status_code == 401
    assert locked.json() == wrong.json()

    reset_limits()
    client.post(
        "/api/v1/followup/access/start", json={"public_id": public_id, "client_key": "once"}
    )
    code = _code(client, auth, public_id)
    first = client.post(
        "/api/v1/followup/access/check",
        json={"public_id": public_id, "code": code, "client_key": "once"},
    )
    second = client.post(
        "/api/v1/followup/access/check",
        json={"public_id": public_id, "code": code, "client_key": "once"},
    )
    assert first.status_code == 200
    assert second.status_code == 401

    reset_limits()
    client.post("/api/v1/followup/access/start", json={"public_id": public_id, "client_key": "old"})
    stale = _code(client, auth, public_id)
    clock.advance(1)
    expired = client.post(
        "/api/v1/followup/access/check",
        json={"public_id": public_id, "code": stale, "client_key": "old"},
    )
    assert expired.status_code == 401
    headers = unlock(client, auth, public_id, "session")
    clock.advance(1)
    assert client.get("/api/v1/followup/me", headers=headers).status_code == 401


def test_worklist_ranks_worse_first_and_scopes_assignment(client, auth, db_session):
    worse = enrol(client, auth)
    late = enrol(client, auth)
    other = db_session.scalar(select(User).where(User.username == "chw"))
    stranger = User(
        username="otherchw",
        password_hash=other.password_hash,
        role="chw",
        display_name="Other CHW",
        department_id=other.department_id,
    )
    db_session.add(stranger)
    db_session.commit()
    hidden = enrol(client, auth, assigned_chw_username="otherchw")
    worse_row = db_session.scalar(
        select(Enrolment).where(Enrolment.public_id == worse["public_id"])
    )
    worse_row.symptom_flag = "worse"
    late_row = db_session.scalar(select(Enrolment).where(Enrolment.public_id == late["public_id"]))
    late_row.opened_at = clock.now() - timedelta(days=9)
    case = db_session.get(CareCase, late_row.case_id)
    case.deadline_at = clock.now() - timedelta(hours=2)
    case.opened_at = late_row.opened_at
    db_session.commit()

    listed = client.get("/api/v1/followup/worklist", headers=auth["chw"])
    assert listed.status_code == 200, listed.text
    body = listed.json()
    ids = [row["public_id"] for row in body["rows"]]
    assert ids[0] == worse["public_id"]
    assert hidden["public_id"] not in ids
    late_item = next(row for row in body["rows"] if row["public_id"] == late["public_id"])
    assert late_item["reason"] == "not arrived, 9 days"
    assert late_item["recommended_action"] in ACTIONS
    assert body["counts"]["worse"] >= 1
    assert body["counts"]["overdue"] >= 1
    blob = json.dumps(body)
    assert PHONE not in blob
    assert "hiv" not in blob

    first = client.post(
        f"/api/v1/followup/worklist/{late['case_id']}/escalate", headers=auth["chw"]
    )
    second = client.post(
        f"/api/v1/followup/worklist/{late['case_id']}/escalate", headers=auth["chw"]
    )
    assert first.status_code == second.status_code == 200
    assert first.json()["task_id"] == second.json()["task_id"]
    count = db_session.scalar(
        select(func.count())
        .select_from(NavigatorTask)
        .where(
            NavigatorTask.case_id == late["case_id"],
            NavigatorTask.task_type == "followup_escalate",
        )
    )
    assert count == 1


def test_safety_checklist(client, auth, db_session):
    opened = enrol(client, auth, channel="web")
    headers = unlock(client, auth, opened["public_id"])
    before = db_session.scalar(select(func.count()).select_from(CareCase))
    danger = client.post(
        "/api/v1/followup/talk",
        json={"message": "I am bleeding", "channel": "web", "language": "en"},
        headers=headers,
    )
    again = client.post(
        "/api/v1/followup/talk",
        json={"message": "I am bleeding", "channel": "web", "language": "en"},
        headers=headers,
    )
    assert danger.status_code == 200, danger.text
    assert "you are fine" not in danger.json()["reply_text"].lower()
    assert "nothing to worry" not in danger.json()["reply_text"].lower()
    assert danger.json()["spoken_text"] == danger.json()["reply_text"]
    assert guide_speaks(danger.json()["reply_text"]) == danger.json()["reply_text"]
    urgent = db_session.scalar(
        select(func.count())
        .select_from(NavigatorTask)
        .where(
            NavigatorTask.case_id == opened["case_id"],
            NavigatorTask.task_type == "followup_urgent",
        )
    )
    assert urgent == 1
    assert again.json()["escalation_label"] == "danger_sign"
    odd = client.post(
        "/api/v1/followup/talk",
        json={"message": "zebrapain99", "channel": "web", "language": "en"},
        headers=headers,
    )
    assert odd.json()["escalation_label"] == "unclear"
    after = db_session.scalar(select(func.count()).select_from(CareCase))
    assert after == before
    for entry in db_session.scalars(select(AuditLog)).all():
        assert "zebrapain99" not in json.dumps(entry.detail or {})
        assert "I am bleeding" not in json.dumps(entry.detail or {})
    stopped = client.post(
        "/api/v1/followup/talk",
        json={"message": "STOP", "channel": "sms", "language": "en"},
        headers=headers,
    )
    assert stopped.status_code == 200
    morning = datetime(2026, 11, 20, 10, 0)
    assert run_checkins(db_session, morning) == 0
    client.post(
        "/api/v1/followup/talk",
        json={"message": "START", "channel": "sms", "language": "en"},
        headers=headers,
    )
    for pack in templates().values():
        for text in pack.values():
            assert problems(text) == []
    for row in db_session.scalars(select(Outbound)).all():
        assert problems(row.body) == []
        assert "hiv" not in row.body.lower()


def test_arrival_is_human_and_lost_needs_a_person(client, auth, db_session):
    opened = enrol(client, auth)
    headers = unlock(client, auth, opened["public_id"])
    denied = client.post(f"/api/v1/followup/facility/{opened['case_id']}/arrive", headers=headers)
    assert denied.status_code in {401, 403}
    chw = client.post(f"/api/v1/followup/facility/{opened['case_id']}/arrive", headers=auth["chw"])
    assert chw.status_code == 403
    arrived = client.post(
        f"/api/v1/followup/facility/{opened['case_id']}/arrive",
        headers=auth["clin"],
    )
    assert arrived.status_code == 200, arrived.text
    assert arrived.json()["state"] == "arrived"
    lost = client.post(f"/api/v1/followup/facility/{opened['case_id']}/lost", headers=auth["nav"])
    assert lost.status_code == 409

    other = enrol(client, auth)
    row = db_session.get(CareCase, other["case_id"])
    row.deadline_at = clock.now() - timedelta(hours=3)
    db_session.commit()
    run_deadline_check(db_session)
    decided = client.post(f"/api/v1/followup/facility/{other['case_id']}/lost", headers=auth["nav"])
    assert decided.status_code == 200, decided.text
    assert decided.json()["state"] == "closed_by_person"


def test_checkins_respect_cadence_quiet_hours_and_stop(client, auth, db_session):
    opened = enrol(client, auth, channel="sms", language="en")
    morning = datetime(2026, 11, 20, 10, 0)
    night = datetime(2026, 11, 20, 22, 0)
    assert run_checkins(db_session, night) == 0
    assert run_checkins(db_session, morning) == 1
    assert run_checkins(db_session, morning) == 0
    later = morning + timedelta(hours=49)
    assert run_checkins(db_session, later) == 1
    row = db_session.scalar(select(Enrolment).where(Enrolment.public_id == opened["public_id"]))
    row.messages_stopped = True
    db_session.commit()
    assert run_checkins(db_session, later + timedelta(hours=49)) == 0
    modes = list(db_session.scalars(select(Outbound.mode_label)))
    assert "template" in modes


def test_telegram_real_update_and_send(client, monkeypatch):
    os.environ["CARELOOP_TELEGRAM_WEBHOOK_SECRET"] = "test-secret"
    sent: dict = {}

    def fake_post(url, json, timeout):
        sent["url"] = url
        sent["json"] = json

        class _Response:
            def raise_for_status(self):
                return None

        return _Response()

    monkeypatch.setenv("CARELOOP_TELEGRAM_BOT_TOKEN", "123456:test-token")
    monkeypatch.setattr("app.modules.followup.telegram.httpx.post", fake_post)
    res = client.post(
        "/api/v1/followup/telegram/webhook",
        json={
            "update_id": 42,
            "message": {
                "message_id": 1,
                "chat": {"id": 9001, "type": "private"},
                "text": "/start",
            },
        },
        headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
    )
    assert res.status_code == 200, res.text
    assert "English" in res.json()["reply_text"]
    assert sent["json"]["chat_id"] == "9001"
    assert sent["json"]["text"] == res.json()["reply_text"]
    assert sent["url"].endswith("/sendMessage")
    assert "test-token" not in res.text
    ignored = client.post(
        "/api/v1/followup/telegram/webhook",
        json={"update_id": 43},
        headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
    )
    assert ignored.status_code == 200, ignored.text
    assert ignored.json()["ok"] is True


def test_telegram_delivers_the_simulated_code(client, auth):
    os.environ["CARELOOP_TELEGRAM_WEBHOOK_SECRET"] = "test-secret"
    os.environ["CARELOOP_EXPOSE_SIMULATED_CODES"] = "true"
    opened = enrol(client, auth, channel="telegram")
    headers = {"X-Telegram-Bot-Api-Secret-Token": "test-secret"}

    def turn(update_id: int, text: str):
        res = client.post(
            "/api/v1/followup/telegram/webhook",
            json={
                "update_id": update_id,
                "message": {"message_id": update_id, "chat": {"id": 77, "type": "private"}, "text": text},
            },
            headers=headers,
        )
        assert res.status_code == 200, res.text
        return res.json()["reply_text"]

    privacy = turn(1, "1")
    assert "encrypted" in privacy.lower()
    assert "card" in turn(2, "OK").lower()
    asked = turn(3, opened["public_id"])
    assert "SIMULATED code:" in asked
    code = asked.split("SIMULATED code:", 1)[1].strip()
    assert code.isdigit() and len(code) == 6


def test_telegram_signature_window_and_stop(client, auth):
    os.environ["CARELOOP_TELEGRAM_WEBHOOK_SECRET"] = "test-secret"
    opened = enrol(client, auth, channel="telegram")
    bad = client.post(
        "/api/v1/followup/telegram/webhook",
        json={"chat_id": "100", "text": "1", "update_id": "u1"},
    )
    assert bad.status_code == 401
    ok = client.post(
        "/api/v1/followup/telegram/webhook",
        json={"chat_id": "100", "text": "1", "update_id": "u1"},
        headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["mode_label"] == "freeform"
    retry = client.post(
        "/api/v1/followup/telegram/webhook",
        json={"chat_id": "100", "text": "1", "update_id": "u1"},
        headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
    )
    assert retry.json()["duplicate"] is True
    sim = client.post(
        "/api/v1/followup/telegram/simulate",
        json={"chat_id": "200", "text": "STOP", "update_id": "s1"},
    )
    assert sim.status_code == 200, sim.text
    assert "STOP" in sim.json()["reply_text"] or "stopped" in sim.json()["reply_text"].lower()
    screen = client.post("/api/v1/followup/ussd", json={"chat_id": "ussd-1", "text": ""})
    assert screen.status_code == 200, screen.text
    assert len(screen.json()["text"]) <= 182
    assert "continue_session" in screen.json()
    assert opened["public_id"]


def test_templates_and_held_out_score_are_honest():
    scored = score_held_out()
    assert scored["misses"] == ["f09", "f10", "f11", "f12"]
    assert scored["hits"] == 7
    assert scored["n"] == 11
    assert scored["recall"] == round(7 / 11, 4)


def test_cohort_is_synthetic_and_not_causal(db_session):
    actor = db_session.scalar(select(User).where(User.username == "clin"))
    build_cohort(db_session, actor, 200)
    payload = report(db_session)
    assert payload["n"] >= 200
    assert payload["synthetic"] is True
    assert "already late" in payload["note"]
    assert "SYNTHETIC" in payload["note"]
    assert set(payload["by_language"]) >= {"en", "sw"}
    assert set(payload["by_channel"]) >= {"telegram", "sms", "ussd", "web"}
    blob = json.dumps(payload)
    assert "0700000000" not in blob
    vault = db_session.scalar(select(func.count()).select_from(ContactVault))
    assert vault >= 200
