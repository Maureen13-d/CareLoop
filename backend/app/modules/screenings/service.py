from sqlalchemy.orm import Session

from app.core import clock
from app.core.config import settings
from app.modules.audit import service as audit
from app.modules.pathways import service as pathways
from app.modules.pathways.loader import load_pathway
from app.modules.patients import service as patients
from app.modules.patients.models import CONSENT_PURPOSE_COORDINATION, Patient
from app.modules.screenings.models import Screening
from app.modules.screenings.schemas import ScreeningIn

OPENS_CASE = ("positive", "suspected_cancer")


def record_screening(db: Session, actor, patient: Patient, data: ScreeningIn):
    """Save a screening result. A positive or suspicious result opens a tracked case,
    unless the patient has not consented to care coordination or a case is already open."""
    performed_at = data.performed_at or clock.now()
    screening = Screening(
        patient_id=patient.id,
        screening_type=data.screening_type,
        result=data.result,
        performed_at=performed_at,
        department_id=actor.department_id,
        recorded_by=actor.id,
    )
    db.add(screening)
    db.flush()
    audit.record(db, actor=actor, action="screening.record", entity_type="screening", entity_id=screening.id,
                 patient_id=patient.id, detail={"type": data.screening_type, "result": data.result})

    if data.result not in OPENS_CASE:
        db.commit()
        return screening, None, "not_required", "Result does not require case tracking."

    pathway = load_pathway()
    existing = pathways.find_open_case(db, patient.id, pathway.id)
    if existing:
        db.commit()
        return screening, existing, "already_open", "An open case already exists for this patient; no new case was created."

    if settings.require_consent_for_tracking and not patients.has_active_consent(db, patient.id, CONSENT_PURPOSE_COORDINATION):
        audit.record(db, actor=actor, action="case.open_blocked", entity_type="screening", entity_id=screening.id,
                     patient_id=patient.id, detail={"reason": "no_consent"}, outcome="rejected")
        db.commit()
        return screening, None, "no_consent", (
            "Result saved, but no case was opened: the patient has not consented to care coordination. "
            "Record consent, then ask a clinician to open the case.")

    case = pathways.open_case(db, patient, screening, actor)
    db.commit()
    return screening, case, "opened", "Case opened."
