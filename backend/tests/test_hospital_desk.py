"""A visit request reaches the simulated clinic, and milestones move the case."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient
from integrations.mock_hospital.app import APPOINTMENTS, TASKS
from integrations.mock_hospital.app import app as hospital

from app.main import app
from app.modules.interop.client import hospital_client

STEPS = ("PATIENT_ENGAGED", "BARRIERS_ASSESSED", "NAVIGATION_ACTIVE")


def test_simulated_clinic_moves_a_case_to_handoff(client, auth, make_case):
    APPOINTMENTS.clear()
    TASKS.clear()
    _patient, recorded = make_case()
    case_id = recorded["case_id"]
    for state in STEPS:
        moved = client.post(
            f"/api/v1/cases/{case_id}/transitions",
            json={"to_state": state, "note": "test"},
            headers=auth["clin"],
        )
        assert moved.status_code == 200, moved.text

    clinic = TestClient(hospital)

    def override():
        yield clinic

    app.dependency_overrides[hospital_client] = override
    try:
        requested = client.post(f"/api/v1/cases/{case_id}/hospital/request", headers=auth["nav"])
        assert requested.status_code == 200, requested.text
        assert requested.json()["milestones"] == []
        case = client.get(f"/api/v1/cases/{case_id}", headers=auth["nav"]).json()
        assert case["state"] == "APPOINTMENT_BOOKED"

        for expected in ("ARRIVAL_CONFIRMED", "ARRIVAL_CONFIRMED", "HANDED_OFF"):
            advanced = client.post(
                f"/api/v1/cases/{case_id}/hospital/advance", headers=auth["clin"]
            )
            assert advanced.status_code == 200, advanced.text
            case = client.get(f"/api/v1/cases/{case_id}", headers=auth["clin"]).json()
            assert case["state"] == expected
        assert advanced.json()["milestones"] == [
            "arrived",
            "assessment-completed",
            "care-started",
        ]
    finally:
        app.dependency_overrides.pop(hospital_client, None)
        clinic.close()


def test_a_visit_cannot_be_requested_before_navigation(client, auth, make_case):
    _patient, recorded = make_case()
    response = client.post(
        f"/api/v1/cases/{recorded['case_id']}/hospital/request", headers=auth["nav"]
    )
    assert response.status_code == 409
