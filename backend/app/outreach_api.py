from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.deps import get_repo
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
from app.repository import Repository

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


def _get_case(repo: Repository, case_id: str) -> Case:
    case = repo.get_case(case_id)
    if case is None:
        raise HTTPException(404, "Case not found")
    return case


def _detail(case: Case, events: list[OutreachEvent]) -> CaseDetail:
    now = datetime.now(UTC)
    return CaseDetail(
        case=CaseView(
            **case.model_dump(), overdue=is_overdue(case.stage, case.stage_entered_at, now)
        ),
        status=case_status(case, events, now),
        next_stages=next_stages(case),
        events=sorted(events, key=lambda e: e.created_at),
    )


@router.get("/queue", response_model=list[OutreachPlan])
def get_queue(repo: Repository = Depends(get_repo)):
    """Dry run: what a sweep would do right now. Most overdue first."""
    log = repo.load_log()
    plans = [p for c in repo.list_cases() if (p := plan_outreach(c, log)) is not None]
    return sorted(plans, key=lambda p: p.days_overdue, reverse=True)


@router.get("/escalated", response_model=list[EscalatedCase])
def list_escalated(repo: Repository = Depends(get_repo)):
    """Cases where automated outreach is exhausted and a human needs to step in."""
    now = datetime.now(UTC)
    log = repo.load_log()
    result = []
    for case in repo.list_cases():
        if case_status(case, log, now) != CaseStatus.ESCALATED:
            continue
        escalated_at = max(
            e.created_at
            for e in log
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
def list_events(
    case_id: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    repo: Repository = Depends(get_repo),
):
    return repo.recent_events(case_id, limit)


@router.post("/sweep", response_model=SweepResult)
def sweep(repo: Repository = Depends(get_repo)):
    cases = repo.list_cases()
    created = run_sweep(cases, repo.load_log(), notifier)
    repo.add_events(created)
    repo.commit()
    return SweepResult(considered=len(cases), created=created)


@router.get("/cases/{case_id}", response_model=CaseDetail)
def get_case_detail(case_id: str, repo: Repository = Depends(get_repo)):
    case = _get_case(repo, case_id)
    return _detail(case, repo.events_for_case(case_id))


@router.post("/cases/{case_id}/send", response_model=OutreachEvent)
def send_one(case_id: str, repo: Repository = Depends(get_repo)):
    case = _get_case(repo, case_id)
    log = repo.events_for_case(case_id)
    plan = plan_outreach(case, log)
    if plan is None:
        raise HTTPException(409, "No outreach is due for this case")
    event = execute(plan, log, notifier)
    repo.add_events([event])
    repo.commit()
    return event


@router.post("/cases/{case_id}/respond", response_model=CaseDetail)
def respond(
    case_id: str,
    body: RespondRequest | None = None,
    repo: Repository = Depends(get_repo),
):
    """Patient attended: advance the stage, reset the ladder, log the response (one transaction)."""
    case = _get_case(repo, case_id)
    log = repo.events_for_case(case_id)
    try:
        event = record_response(case, log, body.to_stage if body else None)
    except AmbiguousTarget as e:
        raise HTTPException(422, str(e)) from e
    except InvalidTransition as e:
        # A double submit lands here: the first request already moved the case.
        raise HTTPException(409, str(e)) from e
    repo.save_case(case)
    repo.add_events([event])
    repo.commit()  # case + event committed together, or neither
    return _detail(case, log)
