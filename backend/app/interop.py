"""I1: bridge from CareLoop to a hospital system over FHIR R4.

SIMULATED. The only "hospital" it talks to is integrations/mock_hospital.
Pure functions plus an injectable httpx client, so it is easy to test and
the real base URL can be swapped in later.
"""
import httpx

FHIR_JSON = "application/fhir+json"


class HospitalRejected(Exception):
    """The hospital system refused the message. The text says why."""


def build_appointment(patient_ref: str, location_ref: str, start_iso: str,
                      description: str = "SYNTHETIC: follow-up visit request") -> dict:
    """Make a FHIR Appointment *request*. Never put a result or diagnosis in here."""
    return {
        "resourceType": "Appointment",
        "status": "proposed",
        "description": description,
        "start": start_iso,
        "participant": [
            {"actor": {"reference": f"Patient/{patient_ref}"}, "status": "needs-action"},
            {"actor": {"reference": f"Location/{location_ref}"}, "status": "needs-action"},
        ],
    }


def send_appointment(client: httpx.Client, appointment: dict) -> str:
    """Send the request. Returns the hospital's appointment id."""
    r = client.post("/fhir/Appointment", json=appointment,
                    headers={"Content-Type": FHIR_JSON})
    if r.status_code != 201:
        raise HospitalRejected(_reason(r))
    return r.json()["id"]


def get_milestones(client: httpx.Client, appointment_id: str) -> list[str]:
    """Milestone codes the hospital has reported, in order (e.g. 'arrived')."""
    r = client.get("/fhir/Task", params={"based-on": f"Appointment/{appointment_id}"})
    if r.status_code != 200:
        raise HospitalRejected(_reason(r))
    return [e["resource"]["code"]["coding"][0]["code"] for e in r.json().get("entry", [])]


def _reason(r: httpx.Response) -> str:
    try:
        return r.json()["issue"][0]["diagnostics"]
    except Exception:
        return f"hospital returned HTTP {r.status_code}"