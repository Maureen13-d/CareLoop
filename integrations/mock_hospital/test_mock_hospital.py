import json
from pathlib import Path

from fastapi.testclient import TestClient

from integrations.mock_hospital.app import app

client = TestClient(app)
SAMPLE = json.loads((Path(__file__).parents[1] / "sample_fhir" / "appointment.json").read_text())


def test_valid_appointment_is_accepted_and_booked():
    r = client.post("/fhir/Appointment", json=SAMPLE)
    assert r.status_code == 201
    assert r.json()["status"] == "booked"


def test_invalid_appointment_gets_clear_error():
    bad = {**SAMPLE, "participant": []}
    r = client.post("/fhir/Appointment", json=bad)
    assert r.status_code == 422
    assert r.json()["resourceType"] == "OperationOutcome"
    assert "participant" in r.json()["issue"][0]["diagnostics"]


def test_wrong_resource_type_rejected():
    r = client.post("/fhir/Appointment", json={"resourceType": "Patient"})
    assert r.status_code == 422


def test_milestones_come_back_in_order():
    appt_id = client.post("/fhir/Appointment", json=SAMPLE).json()["id"]
    q = f"/fhir/Task?based-on=Appointment/{appt_id}"
    assert client.get(q).json()["total"] == 0
    for expected in ["arrived", "assessment-completed", "care-started"]:
        assert client.post(f"/demo/advance/{appt_id}").json()["advanced_to"] == expected
    codes = [e["resource"]["code"]["coding"][0]["code"] for e in client.get(q).json()["entry"]]
    assert codes == ["arrived", "assessment-completed", "care-started"]
    assert client.post(f"/demo/advance/{appt_id}").status_code == 409


def test_task_search_needs_reference():
    assert client.get("/fhir/Task").status_code == 400