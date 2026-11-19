"""Minimal FHIR R4 Task mapping. Validate against a real FHIR server/library before relying on it."""

from app.models import Case
from app.pathway import Stage


def case_to_fhir_task(case: Case) -> dict:
    return {
        "resourceType": "Task",
        "id": case.id,
        "status": "completed" if case.stage == Stage.CLOSED else "in-progress",
        "intent": "plan",
        "description": f"Care pathway stage: {case.stage.value}",
        "for": {"reference": f"Patient/{case.patient_ref}"},
        "authoredOn": case.history[0].at.isoformat() if case.history else None,
        "lastModified": case.stage_entered_at.isoformat(),
    }
