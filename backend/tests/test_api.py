from datetime import UTC, datetime

from app.models import Case, StageEvent
from app.pathway import Stage
from tests.helpers import put_case


def _seed_case():
    now = datetime.now(UTC)
    put_case(
        Case(
            id="case-test",
            patient_ref="SYN-9999",
            stage=Stage.SCREENED,
            stage_entered_at=now,
            history=[StageEvent(stage=Stage.SCREENED, at=now)],
        )
    )


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_list_cases_seeded(client):
    assert len(client.get("/cases").json()) == 25


def test_stage_changes_only_via_respond(client):
    """Invariant the metrics rely on: no route moves a case without logging a response."""
    _seed_case()
    r = client.post("/cases/case-test/advance", json={"to_stage": "abnormal_result"})
    assert r.status_code == 404
    assert client.get("/cases/case-test").json()["stage"] == "screened"


def test_fhir_task(client):
    _seed_case()
    t = client.get("/cases/case-test/fhir-task").json()
    assert t["resourceType"] == "Task" and t["intent"] == "plan"


def test_unknown_case_404(client):
    assert client.get("/cases/nope").status_code == 404
