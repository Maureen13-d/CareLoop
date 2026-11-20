"""The case engine: opens cases, moves them through a pathway, tracks owners and
deadlines, raises escalations, and enforces the evidence-to-close rule.

Rules live here as code, driven by the pathway YAML. AI never calls these functions
to change state; only authenticated staff and the system itself do.

Convention: functions that change a case commit before returning, except `open_case`,
which the caller commits together with the screening that triggered it.
`actor=None` means the system itself (deadline checker, seed script).
"""

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.errors import DomainError
from app.modules.audit import service as audit
from app.modules.auth.models import Department, User
from app.modules.pathways.loader import Pathway, load_pathway
from app.modules.pathways.models import CareCase, CaseEvent, Escalation, Evidence
from app.modules.patients.models import Patient


# ----------------------------------------------------------------- helpers
def _actor_fields(actor) -> dict:
    return {"actor_id": actor.id if actor else None, "actor_type": "user" if actor else "system"}


def _department_id(db: Session, name: str) -> int | None:
    return db.scalar(select(Department.id).where(Department.name == name))


def _reject(
    db: Session,
    actor,
    case: CareCase | None,
    action: str,
    status: int,
    code: str,
    message: str,
    details=None,
    outcome="rejected",
):
    """Record the refused attempt in the audit log, then raise the error."""
    audit.record(
        db,
        actor=actor,
        action=action,
        entity_type="care_case",
        entity_id=case.id if case else None,
        patient_id=case.patient_id if case else None,
        detail={"code": code, **(details or {})},
        outcome=outcome,
    )
    db.commit()
    raise DomainError(status, code, message, details)


def _require_role(
    db: Session, actor, case: CareCase, allowed: tuple[str, ...], action: str
) -> None:
    if actor is not None and actor.role not in allowed:
        _reject(
            db,
            actor,
            case,
            action,
            403,
            "forbidden",
            f"Role '{actor.role}' cannot do this. Allowed: {', '.join(allowed)}",
            {"allowed_roles": list(allowed)},
            outcome="denied",
        )


def get_case(db: Session, case_id: int) -> CareCase:
    case = db.get(CareCase, case_id)
    if not case:
        raise DomainError(404, "not_found", "Case not found")
    return case


def find_open_case(db: Session, patient_id: int, pathway_id: str) -> CareCase | None:
    pw = load_pathway(pathway_id)
    return db.scalar(
        select(CareCase).where(
            CareCase.patient_id == patient_id,
            CareCase.pathway_id == pathway_id,
            CareCase.state.not_in(list(pw.terminal_states)),
        )
    )


def _hours_in_state(target, case: CareCase) -> int:
    """Routine journeys use deadline_hours. Urgent journeys use the shorter wait when set."""
    if case.urgency == "urgent" and target.urgent_deadline_hours is not None:
        return target.urgent_deadline_hours
    return target.deadline_hours


def _apply_state(
    db: Session, pw: Pathway, case: CareCase, to_state: str, actor, note: str | None, now: datetime
) -> None:
    target = pw.states[to_state]
    db.add(
        CaseEvent(
            case_id=case.id,
            from_state=case.state,
            to_state=to_state,
            occurred_at=now,
            note=note,
            **_actor_fields(actor),
        )
    )
    case.state = to_state
    case.state_entered_at = now
    case.deadline_at = now + timedelta(hours=_hours_in_state(target, case))
    case.owner_department_id = _department_id(db, target.owner_department)
    case.owner_user_id = None  # unowned until someone claims it


# ----------------------------------------------------------------- opening
def open_case(
    db: Session, patient: Patient, screening, actor, at: datetime | None = None
) -> CareCase:
    pw = load_pathway()
    now = at or clock.now()
    initial = pw.states[pw.initial_state]
    urgency = "urgent" if screening.result == "suspected_cancer" else "routine"
    hours = initial.deadline_hours
    if urgency == "urgent" and initial.urgent_deadline_hours is not None:
        hours = initial.urgent_deadline_hours
    case = CareCase(
        patient_id=patient.id,
        source_screening_id=screening.id,
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
            note="Case opened from screening result",
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
        detail={"urgency": case.urgency},
        at=at,
    )
    return case


# ----------------------------------------------------------------- moving
def transition(
    db: Session,
    case: CareCase,
    to_state: str,
    actor,
    note: str | None = None,
    at: datetime | None = None,
) -> CareCase:
    pw = load_pathway(case.pathway_id)
    now = at or clock.now()
    action = "case.transition"
    if actor is not None and actor.role == "chw":
        from app.modules.maternal.service import assert_chw_assignment

        assert_chw_assignment(db, actor, case, action)
    if pw.is_terminal(case.state):
        _reject(db, actor, case, action, 409, "case_closed", f"Case is already {case.state}")
    if to_state in pw.terminal_states:
        _reject(
            db,
            actor,
            case,
            action,
            409,
            "invalid_transition",
            "Use the close or mark-lost action to end a case",
            {"to_state": to_state},
        )
    if to_state not in pw.states:
        _reject(
            db,
            actor,
            case,
            action,
            422,
            "unknown_state",
            f"Unknown state '{to_state}'",
            {"to_state": to_state},
        )
    current = pw.states[case.state]
    if to_state not in current.next:
        _reject(
            db,
            actor,
            case,
            action,
            409,
            "invalid_transition",
            f"Case cannot move from {case.state} to {to_state}",
            {"from_state": case.state, "to_state": to_state, "allowed_next": list(current.next)},
        )
    _require_role(db, actor, case, pw.states[to_state].roles, action)

    from_state = case.state
    _apply_state(db, pw, case, to_state, actor, note, now)
    audit.record(
        db,
        actor=actor,
        action=action,
        entity_type="care_case",
        entity_id=case.id,
        patient_id=case.patient_id,
        detail={"from": from_state, "to": to_state},
        at=at,
    )
    db.commit()
    return case


def claim_case(db: Session, case: CareCase, actor) -> CareCase:
    pw = load_pathway(case.pathway_id)
    if pw.is_terminal(case.state):
        _reject(db, actor, case, "case.claim", 409, "case_closed", f"Case is already {case.state}")
    case.owner_user_id = actor.id
    audit.record(
        db,
        actor=actor,
        action="case.claim",
        entity_type="care_case",
        entity_id=case.id,
        patient_id=case.patient_id,
    )
    db.commit()
    return case


# ----------------------------------------------------------------- evidence and closure
def add_evidence(
    db: Session,
    case: CareCase,
    actor,
    type: str,
    description: str,
    reference: str | None = None,
    at: datetime | None = None,
    commit: bool = True,
) -> Evidence:
    pw = load_pathway(case.pathway_id)
    if pw.is_terminal(case.state):
        _reject(
            db, actor, case, "evidence.add", 409, "case_closed", f"Case is already {case.state}"
        )
    if type not in pw.evidence_types:
        _reject(
            db,
            actor,
            case,
            "evidence.add",
            422,
            "unknown_evidence_type",
            f"Evidence type must be one of: {', '.join(pw.evidence_types)}",
            {"allowed": list(pw.evidence_types)},
        )
    evidence = Evidence(
        case_id=case.id,
        type=type,
        description=description,
        reference=reference,
        recorded_by=actor.id if actor else None,
        recorded_at=at or clock.now(),
    )
    db.add(evidence)
    db.flush()
    audit.record(
        db,
        actor=actor,
        action="evidence.add",
        entity_type="care_case",
        entity_id=case.id,
        patient_id=case.patient_id,
        detail={"type": type, "evidence_id": evidence.id},
        at=at,
    )
    if commit:
        db.commit()
    return evidence


def close_case(
    db: Session,
    case: CareCase,
    actor,
    evidence_type: str | None = None,
    description: str | None = None,
    reference: str | None = None,
    note: str | None = None,
    at: datetime | None = None,
) -> CareCase:
    """Close a case. Allowed only from the pathway's closable states, and only with evidence:
    either evidence attached earlier, or evidence supplied in this call."""
    pw = load_pathway(case.pathway_id)
    now = at or clock.now()
    action = "case.close"
    if pw.is_terminal(case.state):
        _reject(db, actor, case, action, 409, "case_closed", f"Case is already {case.state}")
    _require_role(db, actor, case, pw.closure_roles, action)
    if case.state not in pw.closable_from:
        _reject(
            db,
            actor,
            case,
            action,
            409,
            "invalid_transition",
            f"A case cannot be closed from {case.state}",
            {"closable_from": list(pw.closable_from)},
        )

    if evidence_type:
        evidence = add_evidence(
            db, case, actor, evidence_type, description or "", reference, at=at, commit=False
        )
        reason = evidence.type
    else:
        latest = db.scalar(
            select(Evidence)
            .where(Evidence.case_id == case.id, Evidence.type.in_(pw.evidence_types))
            .order_by(Evidence.id.desc())
        )
        if latest is None:
            _reject(
                db,
                actor,
                case,
                action,
                409,
                "evidence_required",
                "A case can only be closed with evidence attached",
                {"evidence_types": list(pw.evidence_types)},
            )
        reason = latest.type

    db.add(
        CaseEvent(
            case_id=case.id,
            from_state=case.state,
            to_state=pw.closed_state,
            occurred_at=now,
            note=note or f"Closed with evidence: {reason}",
            **_actor_fields(actor),
        )
    )
    case.state = pw.closed_state
    case.state_entered_at = now
    case.closed_at = now
    case.closure_reason = reason
    case.deadline_at = None
    case.owner_user_id = None
    audit.record(
        db,
        actor=actor,
        action=action,
        entity_type="care_case",
        entity_id=case.id,
        patient_id=case.patient_id,
        detail={"reason": reason},
        at=at,
    )
    db.commit()
    return case


def decline_case(
    db: Session, case: CareCase, actor, note: str, at: datetime | None = None
) -> CareCase:
    """The patient chose not to proceed. Recorded and respected; never pressured.
    Not available after handoff, when the hospital owns care."""
    pw = load_pathway(case.pathway_id)
    now = at or clock.now()
    action = "case.decline"
    if pw.is_terminal(case.state):
        _reject(db, actor, case, action, 409, "case_closed", f"Case is already {case.state}")
    _require_role(db, actor, case, pw.decline_roles, action)
    if case.state in pw.closable_from:
        _reject(
            db,
            actor,
            case,
            action,
            409,
            "invalid_transition",
            "The patient is already in the hospital's care; CareLoop cannot record a decline here",
        )
    db.add(
        CaseEvent(
            case_id=case.id,
            from_state=case.state,
            to_state=pw.declined_state,
            occurred_at=now,
            note=note,
            **_actor_fields(actor),
        )
    )
    case.state = pw.declined_state
    case.state_entered_at = now
    case.closed_at = now
    case.closure_reason = "patient_declined"
    case.deadline_at = None
    case.owner_user_id = None
    audit.record(
        db,
        actor=actor,
        action=action,
        entity_type="care_case",
        entity_id=case.id,
        patient_id=case.patient_id,
        detail={},
        at=at,
    )
    db.commit()
    return case


def mark_lost(
    db: Session, case: CareCase, actor, note: str, at: datetime | None = None
) -> CareCase:
    """A person decides the patient is lost to follow-up. Software never does this alone."""
    pw = load_pathway(case.pathway_id)
    now = at or clock.now()
    action = "case.mark_lost"
    if pw.is_terminal(case.state):
        _reject(db, actor, case, action, 409, "case_closed", f"Case is already {case.state}")
    _require_role(db, actor, case, pw.lost_roles, action)
    if pw.lost_requires_escalation:
        has_escalation = db.scalar(select(Escalation.id).where(Escalation.case_id == case.id))
        if has_escalation is None:
            _reject(
                db,
                actor,
                case,
                action,
                409,
                "escalation_required",
                "A case can only be marked lost to follow-up after it has been escalated",
            )
    db.add(
        CaseEvent(
            case_id=case.id,
            from_state=case.state,
            to_state=pw.lost_state,
            occurred_at=now,
            note=note,
            **_actor_fields(actor),
        )
    )
    case.state = pw.lost_state
    case.state_entered_at = now
    case.closed_at = now
    case.closure_reason = "lost_to_follow_up"
    case.deadline_at = None
    case.owner_user_id = None
    audit.record(
        db,
        actor=actor,
        action=action,
        entity_type="care_case",
        entity_id=case.id,
        patient_id=case.patient_id,
        detail={},
        at=at,
    )
    db.commit()
    return case


# ----------------------------------------------------------------- escalation
def run_deadline_check(db: Session, now: datetime | None = None) -> list[Escalation]:
    """Find overdue cases and raise escalations. Safe to run repeatedly: an escalation
    level is raised at most once per case and state.

    Routine cases: level 1 when overdue; level 2 when still overdue after the pathway's
    second_level_after_hours. Urgent cases start at the pathway's urgent level."""
    now = now or clock.now()
    overdue = db.scalars(
        select(CareCase).where(CareCase.deadline_at.is_not(None), CareCase.deadline_at < now)
    ).all()
    created: list[Escalation] = []
    for case in overdue:
        pw = load_pathway(case.pathway_id)
        if pw.is_terminal(case.state):
            continue
        hours_over = (now - case.deadline_at).total_seconds() / 3600
        start = pw.urgent_starts_at_level if case.urgency == "urgent" else 1
        level = max(start, 2 if hours_over >= pw.second_level_after_hours else 1)
        for lv in range(start, level + 1):
            exists = db.scalar(
                select(Escalation.id).where(
                    Escalation.case_id == case.id,
                    Escalation.state == case.state,
                    Escalation.level == lv,
                )
            )
            if exists:
                continue
            escalation = Escalation(
                case_id=case.id,
                state=case.state,
                level=lv,
                raised_at=now,
                reason=f"Deadline missed in {case.state} ({hours_over:.0f}h overdue)",
            )
            db.add(escalation)
            db.flush()
            audit.record(
                db,
                actor=None,
                action="escalation.raise",
                entity_type="escalation",
                entity_id=escalation.id,
                patient_id=case.patient_id,
                detail={"case_id": case.id, "level": lv, "state": case.state},
                at=now,
            )
            created.append(escalation)
    db.commit()
    return created


def get_escalation(db: Session, escalation_id: int) -> Escalation:
    escalation = db.get(Escalation, escalation_id)
    if not escalation:
        raise DomainError(404, "not_found", "Escalation not found")
    return escalation


def resolve_escalation(
    db: Session, escalation: Escalation, actor, note: str, at: datetime | None = None
) -> Escalation:
    if escalation.resolved_at is not None:
        raise DomainError(409, "already_resolved", "Escalation is already resolved")
    escalation.resolved_at = at or clock.now()
    escalation.resolved_by = actor.id if actor else None
    escalation.resolution_note = note
    case = db.get(CareCase, escalation.case_id)
    audit.record(
        db,
        actor=actor,
        action="escalation.resolve",
        entity_type="escalation",
        entity_id=escalation.id,
        patient_id=case.patient_id if case else None,
        detail={"case_id": escalation.case_id},
        at=at,
    )
    db.commit()
    return escalation


# ----------------------------------------------------------------- read models
def case_view(db: Session, case: CareCase, now: datetime | None = None) -> dict:
    now = now or clock.now()
    pw = load_pathway(case.pathway_id)
    patient = db.get(Patient, case.patient_id)
    department = db.get(Department, case.owner_department_id) if case.owner_department_id else None
    owner = db.get(User, case.owner_user_id) if case.owner_user_id else None
    terminal = pw.is_terminal(case.state)
    overdue = (not terminal) and case.deadline_at is not None and case.deadline_at < now
    open_escalations = len(
        db.scalars(
            select(Escalation.id).where(
                Escalation.case_id == case.id, Escalation.resolved_at.is_(None)
            )
        ).all()
    )
    return {
        "id": case.id,
        "patient_id": case.patient_id,
        "patient_ref": patient.patient_ref if patient else None,
        "patient_display_name": patient.display_name if patient else None,
        "pathway_id": case.pathway_id,
        "state": case.state,
        "state_label": pw.terminal_states.get(case.state) or pw.states[case.state].label,
        "urgency": case.urgency,
        "owner_user_id": case.owner_user_id,
        "owner_user_name": owner.display_name if owner else None,
        "owner_department": department.label if department else None,
        "unowned": (not terminal) and case.owner_user_id is None,
        "state_entered_at": case.state_entered_at,
        "deadline_at": case.deadline_at,
        "overdue": overdue,
        "hours_overdue": round((now - case.deadline_at).total_seconds() / 3600, 1)
        if overdue
        else None,
        "open_escalations": open_escalations,
        "opened_at": case.opened_at,
        "closed_at": case.closed_at,
        "closure_reason": case.closure_reason,
    }


def list_cases(
    db: Session,
    *,
    state=None,
    urgency=None,
    overdue=None,
    unowned=None,
    mine_user_id=None,
    status="open",
    limit=25,
    offset=0,
) -> list[CareCase]:
    pw = load_pathway()
    now = clock.now()
    terminal = list(pw.terminal_states)
    stmt = select(CareCase).where(CareCase.pathway_id == pw.id)
    if status == "open":
        stmt = stmt.where(CareCase.state.not_in(terminal))
    elif status == "closed":
        stmt = stmt.where(CareCase.state.in_(terminal))
    if state:
        stmt = stmt.where(CareCase.state == state)
    if urgency:
        stmt = stmt.where(CareCase.urgency == urgency)
    if overdue is True:
        stmt = stmt.where(CareCase.state.not_in(terminal), CareCase.deadline_at < now)
    if overdue is False:
        stmt = stmt.where((CareCase.deadline_at.is_(None)) | (CareCase.deadline_at >= now))
    if unowned is True:
        stmt = stmt.where(CareCase.state.not_in(terminal), CareCase.owner_user_id.is_(None))
    if mine_user_id is not None:
        stmt = stmt.where(CareCase.owner_user_id == mine_user_id)
    stmt = (
        stmt.order_by(CareCase.deadline_at.is_(None), CareCase.deadline_at, CareCase.id)
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())


def timeline(db: Session, case: CareCase) -> list[dict]:
    events = db.scalars(
        select(CaseEvent)
        .where(CaseEvent.case_id == case.id)
        .order_by(CaseEvent.occurred_at, CaseEvent.id)
    ).all()
    out = []
    for event in events:
        actor = db.get(User, event.actor_id) if event.actor_id else None
        out.append(
            {
                "id": event.id,
                "from_state": event.from_state,
                "to_state": event.to_state,
                "actor_type": event.actor_type,
                "actor_name": actor.display_name if actor else None,
                "occurred_at": event.occurred_at,
                "note": event.note,
            }
        )
    return out


def escalation_view(db: Session, escalation: Escalation) -> dict:
    case = db.get(CareCase, escalation.case_id)
    patient = db.get(Patient, case.patient_id) if case else None
    return {
        "id": escalation.id,
        "case_id": escalation.case_id,
        "patient_ref": patient.patient_ref if patient else None,
        "state": escalation.state,
        "level": escalation.level,
        "reason": escalation.reason,
        "raised_at": escalation.raised_at,
        "resolved_at": escalation.resolved_at,
        "resolution_note": escalation.resolution_note,
    }
