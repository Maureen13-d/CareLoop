"""I1 tests: CareLoop adapter against the mock hospital (all simulated)."""

import sys
from pathlib import Path

import pytest

# the mock hospital lives in <repo>/integrations, outside backend/
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient
from integrations.mock_hospital.app import app as hospital

from app.interop import (
    HospitalRejected,
    build_appointment,
    get_milestones,
    send_appointment,
)

client = TestClient(hospital)


def test_appointment_goes_out_and_milestones_come_back():
    appt = build_appointment("demo-001", "demo-clinic-1", "2026-11-25T09:00:00+03:00")
    appt_id = send_appointment(client, appt)
    assert get_milestones(client, appt_id) == []
    client.post(f"/demo/advance/{appt_id}")
    client.post(f"/demo/advance/{appt_id}")
    assert get_milestones(client, appt_id) == ["arrived", "assessment-completed"]


def test_invalid_appointment_is_rejected_with_reason():
    appt = build_appointment("demo-001", "demo-clinic-1", "2026-11-25T09:00:00+03:00")
    appt["participant"] = []
    with pytest.raises(HospitalRejected) as err:
        send_appointment(client, appt)
    assert "participant" in str(err.value)


def test_appointment_request_contains_no_result_wording():
    text = str(build_appointment("demo-001", "demo-clinic-1", "2026-11-25T09:00:00+03:00")).lower()
    for word in ["positive", "cancer", "diagnos", "result"]:
        assert word not in text
