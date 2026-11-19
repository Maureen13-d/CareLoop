"""Desk, channels, retrieval and confirmed-worry tasks."""

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, import_models, make_engine
from app.modules.assistant.schemas import AssistantRequest
from app.modules.assistant.service import handle_message
from app.modules.pathways.models import CareCase
from app.workspace_seed import seed_workspace_if_empty

FORBIDDEN = ("cancer", "result", "diagnosis", "positive", "hiv", "screening")


def test_funnel_counts_an_open_case(client, auth, make_case):
    make_case()
    funnel = client.get("/api/v1/analytics/funnel", headers=auth["nav"])
    assert funnel.status_code == 200, funnel.text
    flagged = next(s for s in funnel.json()["stages"] if s["state"] == "SCREENING_FLAGGED")
    assert flagged["count"] >= 1
    summary = client.get("/api/v1/analytics/summary", headers=auth["manager"])
    assert summary.status_code == 200
    assert summary.json()["open_cases"] >= 1


def test_manager_cannot_read_the_task_list(client, auth):
    assert client.get("/api/v1/navigator/tasks", headers=auth["manager"]).status_code == 403


def test_confirming_a_worry_opens_a_task(client, auth):
    resp = client.post(
        "/api/v1/assistant/message",
        json={"channel": "web", "confirm_flag": "cost"},
        headers=auth["nav"],
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["barrier_flags"][0]["status"] == "confirmed"
    tasks = client.get("/api/v1/navigator/tasks", headers=auth["counsellor"]).json()
    assert any(task["task_type"] == "navigator_followup" for task in tasks)
    done = client.patch(
        f"/api/v1/navigator/tasks/{tasks[0]['id']}",
        json={"status": "done"},
        headers=auth["nav"],
    )
    assert done.status_code == 200
    assert done.json()["status"] == "done"


def test_ussd_menu_is_discreet_and_confirms_a_worry(client, auth):
    body = {"session_id": "demo-session", "phone_ref": "+254700000301", "text": ""}
    home = client.post("/api/v1/channels/ussd", json=body)
    assert home.status_code == 200, home.text
    screen = home.json()["text"]
    assert "1 Next step" in screen
    assert len(screen) <= 182
    assert not any(word in screen.lower() for word in FORBIDDEN)

    worry = client.post("/api/v1/channels/ussd", json={**body, "text": "3"})
    assert "2 Cost" in worry.json()["text"]
    chosen = client.post("/api/v1/channels/ussd", json={**body, "text": "2"})
    assert "navigator" in chosen.json()["text"].lower()
    tasks = client.get("/api/v1/navigator/tasks", headers=auth["nav"]).json()
    assert any(task["task_type"] == "navigator_followup" for task in tasks)


def test_sms_reply_codes_stop_and_undelivered(client, auth):
    phone = "+254700000302"
    confirmed = client.post("/api/v1/channels/sms/inbound", json={"phone_ref": phone, "text": "1"})
    assert confirmed.status_code == 200
    assert len(confirmed.json()["body"]) <= 160
    assert "confirm" in confirmed.json()["body"].lower()

    changed = client.post("/api/v1/channels/sms/inbound", json={"phone_ref": phone, "text": "2"})
    assert "change" in changed.json()["body"].lower()

    stopped = client.post("/api/v1/channels/sms/inbound", json={"phone_ref": phone, "text": "STOP"})
    assert stopped.status_code == 200
    silent = client.post(
        "/api/v1/channels/sms/inbound", json={"phone_ref": phone, "text": "hello again"}
    )
    assert silent.status_code == 200
    assert silent.json() is None

    fresh = "+254700000303"
    outbound = client.post(
        "/api/v1/channels/sms/inbound", json={"phone_ref": fresh, "text": "1"}
    ).json()
    missed = client.post(f"/api/v1/channels/sms/{outbound['id']}/undelivered")
    assert missed.status_code == 200
    assert missed.json()["status"] == "undelivered"
    tasks = client.get("/api/v1/navigator/tasks", headers=auth["nav"]).json()
    kinds = {task["task_type"] for task in tasks}
    assert "appointment_change" in kinds
    assert "sms_undelivered" in kinds


def test_web_retrieval_cites_a_passage_and_ignores_small_talk():
    hit = handle_message(AssistantRequest(channel="web", text="what should I bring to the visit"))
    assert hit.tier == "retrieval"
    assert hit.source_ids == ["what_to_bring"]
    assert hit.sources
    assert not any(word in hit.reply_text.lower() for word in FORBIDDEN)

    miss = handle_message(AssistantRequest(channel="web", text="the weather is lovely today"))
    assert miss.tier == "fallback"


def test_seed_spreads_cases_across_the_pathway():
    engine = make_engine("sqlite://", poolclass=StaticPool)
    import_models()
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with Session() as db:
        seed_workspace_if_empty(db, force=True)
        funnel_states = set(db.scalars(select(CareCase.state)).all())
    engine.dispose()
    assert "SCREENING_FLAGGED" in funnel_states
    assert "HANDED_OFF" in funnel_states
    assert "APPOINTMENT_BOOKED" in funnel_states
