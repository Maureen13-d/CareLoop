from datetime import UTC, datetime, timedelta

from app.main import STORE
from app.models import Case, StageEvent
from app.pathway import Stage


def _inject_overdue(case_id="case-od"):
    entered = datetime.now(UTC) - timedelta(days=30)
    STORE[case_id] = Case(
        id=case_id,
        patient_ref="SYN-9001",
        stage=Stage.ABNORMAL_RESULT,
        stage_entered_at=entered,
        history=[StageEvent(stage=Stage.ABNORMAL_RESULT, at=entered)],
    )


def test_queue_contains_overdue_case(client):
    _inject_overdue()
    ids = [p["case_id"] for p in client.get("/outreach/queue").json()]
    assert "case-od" in ids


def test_sweep_logs_events_and_is_idempotent(client):
    _inject_overdue()
    first = client.post("/outreach/sweep").json()
    assert any(e["case_id"] == "case-od" for e in first["created"])
    assert client.post("/outreach/sweep").json()["created"] == []
    events = client.get("/outreach/events", params={"case_id": "case-od"}).json()
    assert len(events) == 1 and events[0]["channel"] == "sms"


def test_send_one_then_conflict(client):
    _inject_overdue()
    assert client.post("/outreach/cases/case-od/send").status_code == 200
    assert client.post("/outreach/cases/case-od/send").status_code == 409


def test_send_unknown_case_404(client):
    assert client.post("/outreach/cases/nope/send").status_code == 404


def test_all_logged_events_are_synthetic(client):
    client.post("/outreach/sweep")
    events = client.get("/outreach/events", params={"limit": 500}).json()
    assert all(e["patient_ref"].startswith("SYN-") for e in events)
