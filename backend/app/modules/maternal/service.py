"""Open a maternal journey and list the women a caller is allowed to see."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.errors import DomainError
from app.modules.audit import service as audit
from app.modules.auth.models import ROLE_CHW, User
from app.modules.maternal.models import Pregnancy, Reading
from app.modules.pathways.loader import load_pathway
from app.modules.pathways.models import CareCase, CaseEvent
from app.modules.pathways.service import _department_id, find_open_case
from app.modules.patients.models import Patient


def assert_chw_assignment(db: Session, actor: User, case: CareCase, action: str) -> None:
    """A promoter may act only on women assigned to them."""
    from app.modules.pathways.service import _reject

    assigned = db.scalar(
        select(Pregnancy.id).where(
            Pregnancy.patient_id == case.patient_id,
            Pregnancy.assigned_chw_id == actor.id,
        )
    )
    if assigned is None:
        _reject(
            db,
            actor,
            case,
            action,
            403,
            "forbidden",
            "This person is not assigned to you",
        )


def open_maternal_case(
    db: Session,
    patient: Patient,
    pregnancy: Pregnancy,
    actor: User | None,
    urgency: str = "routine",
) -> CareCase:
    """Open one maternal journey. A human or the system may open it. Software does not close it."""
    if pregnancy.patient_id != patient.id:
        raise DomainError(422, "pregnancy_mismatch", "That pregnancy is not for this person")
    if urgency not in {"routine", "urgent"}:
        raise DomainError(422, "bad_urgency", "Urgency must be routine or urgent")
    if not pregnancy.consent_care_coordination:
        raise DomainError(
            409,
            "consent_required",
            "Care coordination consent is required before a journey opens",
        )
    pw = load_pathway("maternal")
    allowed = pw.states[pw.initial_state].roles
    if actor is not None and actor.role not in allowed:
        audit.record(
            db,
            actor=actor,
            action="case.open",
            entity_type="care_case",
            patient_id=patient.id,
            detail={"allowed_roles": list(allowed)},
            outcome="denied",
        )
        db.commit()
        raise DomainError(403, "forbidden", f"Role '{actor.role}' cannot open a maternal journey")
    if find_open_case(db, patient.id, "maternal") is not None:
        raise DomainError(409, "case_open", "This person already has an open maternal journey")

    now = clock.now()
    initial = pw.states[pw.initial_state]
    hours = initial.deadline_hours
    if urgency == "urgent" and initial.urgent_deadline_hours is not None:
        hours = initial.urgent_deadline_hours
    case = CareCase(
        patient_id=patient.id,
        source_screening_id=None,
        pathway_id=pw.id,
        pathway_version=pw.version,
        state=pw.initial_state,
        urgency=urgency,
        owner_department_id=_department_id(db, initial.owner_department),
        state_entered_at=now,
        deadline_at=now + timedelta(hours=hours),
        opened_at=now,
    )
    db.add(case)
    db.flush()
    db.add(
        CaseEvent(
            case_id=case.id,
            from_state=None,
            to_state=pw.initial_state,
            actor_id=actor.id if actor else None,
            actor_type="user" if actor else "system",
            occurred_at=now,
            note="Maternal journey opened",
        )
    )
    audit.record(
        db,
        actor=actor,
        action="case.open",
        entity_type="care_case",
        entity_id=case.id,
        patient_id=patient.id,
        detail={"pathway": "maternal", "urgency": urgency},
    )
    db.commit()
    return case


def list_pregnancies(db: Session, actor: User) -> list[dict]:
    """A promoter sees only women assigned to them. Navigators and clinicians see the demo list."""
    stmt = select(Pregnancy).order_by(Pregnancy.id)
    if actor.role == ROLE_CHW:
        stmt = stmt.where(Pregnancy.assigned_chw_id == actor.id)
    rows = []
    for pregnancy in db.scalars(stmt).all():
        patient = db.get(Patient, pregnancy.patient_id)
        case = db.scalar(
            select(CareCase)
            .where(CareCase.patient_id == pregnancy.patient_id, CareCase.pathway_id == "maternal")
            .order_by(CareCase.id.desc())
        )
        reading = db.scalar(
            select(Reading).where(Reading.pregnancy_id == pregnancy.id).order_by(Reading.id.desc())
        )
        rows.append(
            {
                "id": pregnancy.id,
                "patient_ref": patient.patient_ref if patient else "",
                "display_name": patient.display_name if patient else "",
                "gestation_band": pregnancy.gestation_band,
                "area_label": pregnancy.area_label,
                "case_id": case.id if case else None,
                "case_state": case.state if case else None,
                "urgency": case.urgency if case else None,
                "risk_level": reading.risk_level if reading else None,
            }
        )
    return rows
