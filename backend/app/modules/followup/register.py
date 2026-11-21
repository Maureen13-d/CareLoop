"""Record a screening decision and, when follow-up is accepted, issue a public ID."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.errors import DomainError
from app.modules.audit import service as audit
from app.modules.auth.models import User
from app.modules.followup.ids import new_public_id
from app.modules.followup.journey import open_followup
from app.modules.followup.models import ContactVault, Enrolment
from app.modules.followup.schemas import RegisterIn
from app.modules.followup.texts import slip_lines
from app.modules.patients.models import CONSENT_PURPOSE_COORDINATION, Consent, Patient

OPENS = {"concerning", "urgent"}


def register_followup(
    db: Session, actor, data: RegisterIn, *, public_id: str | None = None
) -> dict:
    """public_id is for the fixed demo card only; normal cards get a fresh random ID."""
    if data.finding not in OPENS:
        audit.record(
            db,
            actor=actor,
            action="followup.not_required",
            entity_type="followup",
            detail={"finding": data.finding},
        )
        db.commit()
        return {"status": "not_required", "public_id": None, "case_id": None, "slip": []}

    if not data.consent:
        audit.record(
            db,
            actor=actor,
            action="followup.no_consent",
            entity_type="followup",
            detail={"finding": data.finding},
            outcome="rejected",
        )
        db.commit()
        return {"status": "no_consent", "public_id": None, "case_id": None, "slip": []}

    if len(data.contact.strip()) < 3:
        raise DomainError(
            422, "contact_required", "A contact is required when follow-up is accepted"
        )

    public_id = public_id or new_public_id()
    now = clock.now()
    patient = Patient(
        patient_ref=public_id,
        display_name="SYNTHETIC",
        age_band=data.age_band,
        zone=data.area_label,
        preferred_language=data.language,
        is_synthetic=True,
    )
    db.add(patient)
    db.flush()
    db.add(
        Consent(
            patient_id=patient.id,
            purpose=CONSENT_PURPOSE_COORDINATION,
            granted=True,
            granted_at=now,
        )
    )
    db.add(ContactVault(public_id=public_id, contact_ref=data.contact.strip(), created_at=now))
    urgency = "urgent" if data.finding == "urgent" else "routine"
    case = open_followup(db, patient, actor, urgency)
    chw_id = None
    if data.assigned_chw_username:
        chw = db.scalar(
            select(User).where(
                User.username == data.assigned_chw_username,
                User.role == "chw",
            )
        )
        chw_id = chw.id if chw else None
    enrolment = Enrolment(
        patient_id=patient.id,
        public_id=public_id,
        case_id=case.id,
        screening_type=data.screening_type,
        finding=data.finding,
        language=data.language,
        channel=data.channel,
        area_label=data.area_label,
        assigned_chw_id=chw_id,
        opened_at=now,
    )
    db.add(enrolment)
    db.flush()
    audit.record(
        db,
        actor=actor,
        action="followup.open",
        entity_type="followup",
        entity_id=enrolment.id,
        patient_id=patient.id,
        detail={"finding": data.finding, "language": data.language, "channel": data.channel},
    )
    db.commit()
    return {
        "status": "opened",
        "public_id": public_id,
        "case_id": case.id,
        "slip": slip_lines(data.language),
    }
