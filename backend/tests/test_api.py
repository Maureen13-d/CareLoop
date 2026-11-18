from datetime import UTC, datetime

from app.main import STORE
from app.models import Case, StageEvent
from app.pathway import Stage


def _seed_case():
    now = datetime.now(UTC)
    STORE["case-test"] = Case(id="case-test", patient_ref="SYN-9999", stage=Stage.SCREENED,
                              stage_entered_at=now,
                              history=[StageEvent(stage=Stage.SCREENED, at=now)])
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"
def test_list_cases_seeded(client):
    assert len(client.get("/cases").json()) > 0
def test_advance_flow(client):
    _seed_case()
    bad = client.post("/cases/case-test/advance", json={"to_stage": "treatment_started"})
    assert bad.status_code == 409
    ok = client.post("/cases/case-test/advance", json={"to_stage": "abnormal_result"})
    assert ok.status_code == 200 and ok.json()["stage"] == "abnormal_result"
def test_fhir_task(client):
    _seed_case()
    t = client.get("/cases/case-test/fhir-task").json()
    assert t["resourceType"] == "Task" and t["intent"] == "plan"
def test_unknown_case_404(client):
    assert client.get("/cases/nope").status_code == 404
