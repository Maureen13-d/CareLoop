from datetime import UTC, datetime, timedelta

from app.demo import seed_demo_scenario
from app.models import Case, StageEvent
from app.pathway import Stage
from tests.helpers import put_case


def _inject(case_id="case-od", stage=Stage.ABNORMAL_RESULT, days=30):
    entered = datetime.now(UTC) - timedelta(days=days)
    put_case(
        Case(
            id=case_id,
            patient_ref="SYN-9001",
            stage=stage,
            stage_entered_at=entered,
            history=[StageEvent(stage=stage, at=entered)],
        )
    )


def _seed_demo():
    store: dict[str, Case] = {}
    log = []
    seed_demo_scenario(store, log)
    put_case(store["case-demo"], log)


def test_respond_closes_the_loop(client):
    _inject()
    client.post("/outreach/sweep")
    before = client.get("/outreach/cases/case-od").json()
    assert before["status"] == "overdue"
    r = client.post("/outreach/cases/case-od/respond")  # single path: no body needed
    assert r.status_code == 200
    after = r.json()
    assert after["status"] == "on_track"
    assert after["case"]["stage"] == "referred"
    assert after["next_stages"] == ["diagnostic_done"]
    assert after["events"][-1]["kind"] == "response"
    queue_ids = [p["case_id"] for p in client.get("/outreach/queue").json()]
    assert "case-od" not in queue_ids


def test_ambiguous_stage_returns_422_then_accepts_a_choice(client):
    _inject(stage=Stage.SCREENED)
    assert client.post("/outreach/cases/case-od/respond").status_code == 422
    r = client.post("/outreach/cases/case-od/respond", json={"to_stage": "closed"})
    assert r.status_code == 200 and r.json()["status"] == "closed"


def test_invalid_target_returns_409(client):
    _inject()
    r = client.post("/outreach/cases/case-od/respond", json={"to_stage": "treatment_started"})
    assert r.status_code == 409


def test_repeated_response_is_rejected(client):
    _inject()
    body = {"to_stage": "referred"}
    assert client.post("/outreach/cases/case-od/respond", json=body).status_code == 200
    assert client.post("/outreach/cases/case-od/respond", json=body).status_code == 409


def test_unknown_case_returns_404(client):
    assert client.post("/outreach/cases/nope/respond").status_code == 404
    assert client.get("/outreach/cases/nope").status_code == 404


def test_demo_scenario_escalated_then_recovered(client):
    _seed_demo()
    escalated = [e["case_id"] for e in client.get("/outreach/escalated").json()]
    assert "case-demo" in escalated
    detail = client.get("/outreach/cases/case-demo").json()
    assert detail["status"] == "escalated"
    kinds = [e["kind"] for e in detail["events"]]
    assert kinds == ["reminder", "reminder", "reminder", "escalation"]
    done = client.post("/outreach/cases/case-demo/respond").json()
    assert done["status"] == "on_track"
    assert "case-demo" not in [e["case_id"] for e in client.get("/outreach/escalated").json()]
