from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.errors import DomainError
from app.modules.audit import service as audit
from app.modules.patients.models import Consent, Patient
from app.modules.patients.schemas import ConsentIn, PatientCreate


def get_patient(db: Session, patient_id: int) -> Patient:
    patient = db.get(Patient, patient_id)
    if not patient:
        raise DomainError(404, "not_found", "Patient not found")
    return patient


def create_patient(db: Session, actor, data: PatientCreate) -> Patient:
    next_number = (db.scalar(select(func.max(Patient.id))) or 0) + 1
    patient = Patient(
        patient_ref=f"CL-{next_number:06d}",
        display_name=data.display_name,
        age_band=data.age_band,
        zone=data.zone,
        preferred_language=data.preferred_language,
    )
    db.add(patient)
    db.flush()
    audit.record(
        db,
        actor=actor,
        action="patient.create",
        entity_type="patient",
        entity_id=patient.id,
        patient_id=patient.id,
    )
    db.commit()
    return patient


def has_active_consent(db: Session, patient_id: int, purpose: str) -> bool:
    return (
        db.scalar(
            select(Consent.id).where(
                Consent.patient_id == patient_id,
                Consent.purpose == purpose,
                Consent.granted.is_(True),
                Consent.revoked_at.is_(None),
            )
        )
        is not None
    )


def record_consent(db: Session, actor, patient: Patient, data: ConsentIn, at=None) -> Consent:
    """Grant creates a record. Withdrawal revokes the active record(s); history is kept."""
    now = at or clock.now()
    if data.granted:
        consent = Consent(patient_id=patient.id, purpose=data.purpose, granted=True, granted_at=now)
        db.add(consent)
    else:
        active = db.scalars(
            select(Consent).where(
                Consent.patient_id == patient.id,
                Consent.purpose == data.purpose,
                Consent.granted.is_(True),
                Consent.revoked_at.is_(None),
            )
        ).all()
        if not active:
            raise DomainError(
                409, "no_active_consent", "There is no active consent to withdraw for this purpose"
            )
        for consent in active:
            consent.granted = False
            consent.revoked_at = now
        consent = active[-1]
    db.flush()
    audit.record(
        db,
        actor=actor,
        action="consent.grant" if data.granted else "consent.revoke",
        entity_type="consent",
        entity_id=consent.id,
        patient_id=patient.id,
        detail={"purpose": data.purpose},
        at=at,
    )
    db.commit()
    return consent
