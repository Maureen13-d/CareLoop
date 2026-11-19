from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.models import Case, CaseView
from app.outreach import (
    AmbiguousTarget,
    CaseStatus,
    Kind,
    OutreachEvent,
    OutreachPlan,
    SimulatedNotifier,
    case_status,
    execute,
    next_stages,
    plan_outreach,
    record_response,
    run_sweep,
)
from app.pathway import SLA_DAYS, InvalidTransition, Stage, is_overdue
from app.store import OUTREACH_LOG, STORE

router = APIRouter(prefix="/outreach", tags=["outreach"])
notifier = SimulatedNotifier()


class SweepResult(BaseModel):
    considered: int
    created: list[OutreachEvent]


class RespondRequest(BaseModel):
    # An enum only, deliberately no free-text field (PHI risk). See docs/DATA_POLICY.md.
    to_stage: Stage | None = None


class CaseDetail(BaseModel):
    case: CaseView
    status: CaseStatus
    next_stages: list[Stage]
    events: list[OutreachEvent]  # oldest first


class EscalatedCase(BaseModel):
    case_id: str
    patient_ref: str
    stage: Stage
    days_overdue: int
    escalated_at: datetime


def _get_case(case_id: str) -> Case:
    case = STORE.get(case_id)
    if case is None:
        raise HTTPException(404, "Case not found")
    return case


def _detail(case: Case) -> CaseDetail:
    now = datetime.now(UTC)
    events = sorted((e for e in OUTREACH_LOG if e.case_id == case.id), key=lambda e: e.created_at)
    return CaseDetail(
        case=CaseView(
            **case.model_dump(), overdue=is_overdue(case.stage, case.stage_entered_at, now)
        ),
        status=case_status(case, OUTREACH_LOG, now),
        next_stages=next_stages(case),
        events=events,
    )


@router.get("/queue", response_model=list[OutreachPlan])
def get_queue():
    """Dry run: what a sweep would do right now. Most overdue first."""
    plans = [p for c in STORE.values() if (p := plan_outreach(c, OUTREACH_LOG)) is not None]
    return sorted(plans, key=lambda p: p.days_overdue, reverse=True)


@router.get("/escalated", response_model=list[EscalatedCase])
def list_escalated():
    """Cases where automated outreach is exhausted and a human needs to step in."""
    now = datetime.now(UTC)
    result = []
    for case in STORE.values():
        if case_status(case, OUTREACH_LOG, now) != CaseStatus.ESCALATED:
            continue
        escalated_at = max(
            e.created_at
            for e in OUTREACH_LOG
            if e.case_id == case.id and e.kind == Kind.ESCALATION and e.stage == case.stage
        )
        result.append(
            EscalatedCase(
                case_id=case.id,
                patient_ref=case.patient_ref,
                stage=case.stage,
                days_overdue=max((now - case.stage_entered_at).days - SLA_DAYS[case.stage], 0),
                escalated_at=escalated_at,
            )
        )
    return sorted(result, key=lambda c: c.days_overdue, reverse=True)


@router.get("/events", response_model=list[OutreachEvent])
def list_events(case_id: str | None = None, limit: int = Query(50, ge=1, le=500)):
    items = [e for e in OUTREACH_LOG if case_id is None or e.case_id == case_id]
    return sorted(items, key=lambda e: e.created_at, reverse=True)[:limit]


@router.post("/sweep", response_model=SweepResult)
def sweep():
    created = run_sweep(list(STORE.values()), OUTREACH_LOG, notifier)
    return SweepResult(considered=len(STORE), created=created)


@router.get("/cases/{case_id}", response_model=CaseDetail)
def get_case_detail(case_id: str):
    return _detail(_get_case(case_id))


@router.post("/cases/{case_id}/send", response_model=OutreachEvent)
def send_one(case_id: str):
    case = _get_case(case_id)
    plan = plan_outreach(case, OUTREACH_LOG)
    if plan is None:
        raise HTTPException(409, "No outreach is due for this case")
    return execute(plan, OUTREACH_LOG, notifier)


@router.post("/cases/{case_id}/respond", response_model=CaseDetail)
def respond(case_id: str, body: RespondRequest | None = None):
    """Patient attended: advance the stage, reset the ladder, log the response."""
    case = _get_case(case_id)
    try:
        record_response(case, OUTREACH_LOG, body.to_stage if body else None)
    except AmbiguousTarget as e:
        raise HTTPException(422, str(e)) from e
    except InvalidTransition as e:
        raise HTTPException(409, str(e)) from e
    return _detail(case)
