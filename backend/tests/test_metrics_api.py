from app.demo import seed_demo_scenario
from app.models import Case
from tests.helpers import put_case


def _seed_demo():
    store: dict[str, Case] = {}
    log = []
    seed_demo_scenario(store, log)
    put_case(store["case-demo"], log)


def test_metrics_with_no_outreach_yet(client):
    m = client.get("/metrics").json()
    assert m["total_cases"] == 25
    assert m["loop_closure"]["contacted_episodes"] == 0
    assert m["loop_closure"]["closure_rate"] is None
    assert "synthetic" in m["disclaimer"].lower()


def test_metrics_follow_the_demo_story(client):
    _seed_demo()
    before = client.get("/metrics").json()
    assert before["escalation"]["escalated"] == 1
    assert before["escalation"]["awaiting_coordinator"] == 1
    assert before["loop_closure"]["closure_rate"] == 0.0  # 0 of 1 attended so far
    assert client.post("/outreach/cases/case-demo/respond").status_code == 200
    after = client.get("/metrics").json()
    assert after["loop_closure"]["closure_rate"] == 1.0
    assert after["loop_closure"]["median_contacts_to_attend"] == 4.0
    assert after["loop_closure"]["attended_by_last_channel"]["coordinator"] == 1
    assert after["escalation"]["recovery_rate"] == 1.0
    assert after["escalation"]["awaiting_coordinator"] == 0
    assert after["loop_closure"]["unrecorded_advances"] == 0
