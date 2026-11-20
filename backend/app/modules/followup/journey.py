"""Open a follow-up case on the generic pathway. Does not touch cervical or maternal."""

from datetime import timedelta

from sqlalchemy.orm import Session

from app.core import clock
from app.modules.audit import service as audit
from app.modules.pathways.loader import load_pathway
from app.modules.pathways.models import CareCase, CaseEvent
from app.modules.pathways.service import _actor_fields, _department_id


def open_followup(db: Session, patient, actor, urgency: str) -> CareCase:
    pw = load_pathway("follow_up")
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
            occurred_at=now,
            note="follow-up opened",
            **_actor_fields(actor),
        )
    )
    audit.record(
        db,
        actor=actor,
        action="case.open",
        entity_type="care_case",
        entity_id=case.id,
        patient_id=patient.id,
        detail={"pathway": "follow_up", "urgency": urgency},
    )
    return case
