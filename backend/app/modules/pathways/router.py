from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.db import get_db
from app.core.deps import get_current_user, require_roles
from app.core.errors import DomainError
from app.modules.audit import service as audit
from app.modules.auth.models import ROLE_ADMIN, ROLE_CHW, ROLE_CLINICIAN, ROLE_NAVIGATOR
from app.modules.pathways import service
from app.modules.pathways.loader import PathwayError, load_pathway
from app.modules.pathways.models import Escalation
from app.modules.pathways.schemas import (
    AdvanceClockIn,
    CaseOut,
    ClockOut,
    CloseIn,
    DeadlineCheckOut,
    DeclineIn,
    EscalationOut,
    EventOut,
    EvidenceIn,
    EvidenceOut,
    LostIn,
    PathwayOut,
    PathwayStateOut,
    ResolveIn,
    TransitionIn,
)

staff = require_roles(ROLE_NAVIGATOR, ROLE_CLINICIAN)
readers = require_roles(ROLE_NAVIGATOR, ROLE_CLINICIAN, ROLE_ADMIN)
movers = require_roles(ROLE_NAVIGATOR, ROLE_CLINICIAN, ROLE_CHW)

router = APIRouter(prefix="/cases", tags=["cases"])
escalation_router = APIRouter(prefix="/escalations", tags=["escalations"])
pathway_router = APIRouter(prefix="/pathways", tags=["pathways"])
admin_router = APIRouter(prefix="/admin", tags=["admin (demo controls)"])


# ------------------------------------------------------------------ cases
@router.get("", response_model=list[CaseOut])
def list_cases(
    state: str | None = None,
    urgency: str | None = Query(None, pattern="^(routine|urgent)$"),
    overdue: bool | None = None,
    unowned: bool | None = None,
    mine: bool = False,
    status: str = Query("open", pattern="^(open|closed|all)$"),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user=Depends(readers),
):
    cases = service.list_cases(
        db,
        state=state,
        urgency=urgency,
        overdue=overdue,
        unowned=unowned,
        mine_user_id=user.id if mine else None,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [service.case_view(db, c) for c in cases]


@router.get("/{case_id}", response_model=CaseOut)
def get_case(case_id: int, db: Session = Depends(get_db), user=Depends(staff)):
    case = service.get_case(db, case_id)
    audit.record(
        db,
        actor=user,
        action="case.view",
        entity_type="care_case",
        entity_id=case.id,
        patient_id=case.patient_id,
    )
    db.commit()
    return service.case_view(db, case)


@router.get("/{case_id}/timeline", response_model=list[EventOut])
def get_timeline(case_id: int, db: Session = Depends(get_db), _=Depends(staff)):
    return service.timeline(db, service.get_case(db, case_id))


@router.post("/{case_id}/transitions", response_model=CaseOut)
def post_transition(
    case_id: int, data: TransitionIn, db: Session = Depends(get_db), user=Depends(movers)
):
    case = service.transition(db, service.get_case(db, case_id), data.to_state, user, data.note)
    return service.case_view(db, case)


@router.post("/{case_id}/claim", response_model=CaseOut)
def post_claim(case_id: int, db: Session = Depends(get_db), user=Depends(staff)):
    return service.case_view(db, service.claim_case(db, service.get_case(db, case_id), user))


@router.post("/{case_id}/evidence", response_model=EvidenceOut, status_code=201)
def post_evidence(
    case_id: int, data: EvidenceIn, db: Session = Depends(get_db), user=Depends(staff)
):
    return service.add_evidence(
        db, service.get_case(db, case_id), user, data.type, data.description, data.reference
    )


@router.post("/{case_id}/close", response_model=CaseOut)
def post_close(case_id: int, data: CloseIn, db: Session = Depends(get_db), user=Depends(staff)):
    case = service.close_case(
        db,
        service.get_case(db, case_id),
        user,
        data.evidence_type,
        data.description,
        data.reference,
        data.note,
    )
    return service.case_view(db, case)


@router.post("/{case_id}/decline", response_model=CaseOut)
def post_decline(case_id: int, data: DeclineIn, db: Session = Depends(get_db), user=Depends(staff)):
    return service.case_view(
        db, service.decline_case(db, service.get_case(db, case_id), user, data.note)
    )


@router.post("/{case_id}/mark-lost", response_model=CaseOut)
def post_mark_lost(case_id: int, data: LostIn, db: Session = Depends(get_db), user=Depends(staff)):
    return service.case_view(
        db, service.mark_lost(db, service.get_case(db, case_id), user, data.note)
    )


# ------------------------------------------------------------------ escalations
@escalation_router.get("", response_model=list[EscalationOut])
def list_escalations(
    resolved: bool | None = False,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _=Depends(readers),
):
    stmt = select(Escalation).order_by(Escalation.level.desc(), Escalation.raised_at)
    if resolved is True:
        stmt = stmt.where(Escalation.resolved_at.is_not(None))
    elif resolved is False:
        stmt = stmt.where(Escalation.resolved_at.is_(None))
    return [
        service.escalation_view(db, e) for e in db.scalars(stmt.limit(limit).offset(offset)).all()
    ]


@escalation_router.post("/{escalation_id}/resolve", response_model=EscalationOut)
def resolve(
    escalation_id: int, data: ResolveIn, db: Session = Depends(get_db), user=Depends(staff)
):
    escalation = service.resolve_escalation(
        db, service.get_escalation(db, escalation_id), user, data.note
    )
    return service.escalation_view(db, escalation)


# ------------------------------------------------------------------ pathway definition
@pathway_router.get("/{pathway_id}", response_model=PathwayOut)
def get_pathway(pathway_id: str, _=Depends(get_current_user)):
    try:
        pw = load_pathway(pathway_id)
    except PathwayError:
        raise DomainError(404, "not_found", "Pathway not found")
    return PathwayOut(
        id=pw.id,
        name=pw.name,
        version=pw.version,
        deadlines_status=pw.deadlines_status,
        initial_state=pw.initial_state,
        terminal_states=pw.terminal_states,
        states=[
            PathwayStateOut(
                name=s.name,
                label=s.label,
                owner_department=s.owner_department,
                deadline_hours=s.deadline_hours,
                urgent_deadline_hours=s.urgent_deadline_hours,
                next=list(s.next),
                roles=list(s.roles),
            )
            for s in pw.states.values()
        ],
    )


# ------------------------------------------------------------------ admin / demo controls
admin_only = require_roles(ROLE_ADMIN)


@admin_router.get("/clock", response_model=ClockOut)
def get_clock(_=Depends(admin_only)):
    return ClockOut(demo_now=clock.now(), offset_hours=clock.offset_hours())


@admin_router.post("/advance-clock", response_model=ClockOut)
def advance_clock(data: AdvanceClockIn, db: Session = Depends(get_db), user=Depends(admin_only)):
    clock.advance(data.hours)
    audit.record(
        db,
        actor=user,
        action="demo.advance_clock",
        entity_type="clock",
        detail={"hours": data.hours},
    )
    db.commit()
    return ClockOut(demo_now=clock.now(), offset_hours=clock.offset_hours())


@admin_router.post("/reset-clock", response_model=ClockOut)
def reset_clock(db: Session = Depends(get_db), user=Depends(admin_only)):
    clock.reset()
    audit.record(db, actor=user, action="demo.reset_clock", entity_type="clock")
    db.commit()
    return ClockOut(demo_now=clock.now(), offset_hours=clock.offset_hours())


@admin_router.post("/run-deadline-check", response_model=DeadlineCheckOut)
def run_check(db: Session = Depends(get_db), user=Depends(admin_only)):
    created = service.run_deadline_check(db)
    audit.record(
        db,
        actor=user,
        action="demo.run_deadline_check",
        entity_type="escalation",
        detail={"created": len(created)},
    )
    db.commit()
    return DeadlineCheckOut(escalations_created=len(created))
