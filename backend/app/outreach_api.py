from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.outreach import (
    OutreachEvent,
    OutreachPlan,
    SimulatedNotifier,
    execute,
    plan_outreach,
    run_sweep,
)
from app.store import OUTREACH_LOG, STORE

router = APIRouter(prefix="/outreach", tags=["outreach"])
notifier = SimulatedNotifier()


class SweepResult(BaseModel):
    considered: int
    created: list[OutreachEvent]


@router.get("/queue", response_model=list[OutreachPlan])
def get_queue():
    """Dry run: what a sweep would do right now. Most overdue first."""
    plans = [p for c in STORE.values() if (p := plan_outreach(c, OUTREACH_LOG)) is not None]
    return sorted(plans, key=lambda p: p.days_overdue, reverse=True)


@router.get("/events", response_model=list[OutreachEvent])
def list_events(case_id: str | None = None, limit: int = Query(50, ge=1, le=500)):
    items = [e for e in OUTREACH_LOG if case_id is None or e.case_id == case_id]
    return sorted(items, key=lambda e: e.created_at, reverse=True)[:limit]


@router.post("/sweep", response_model=SweepResult)
def sweep():
    created = run_sweep(list(STORE.values()), OUTREACH_LOG, notifier)
    return SweepResult(considered=len(STORE), created=created)


@router.post("/cases/{case_id}/send", response_model=OutreachEvent)
def send_one(case_id: str):
    case = STORE.get(case_id)
    if case is None:
        raise HTTPException(404, "Case not found")
    plan = plan_outreach(case, OUTREACH_LOG)
    if plan is None:
        raise HTTPException(409, "No outreach is due for this case")
    return execute(plan, OUTREACH_LOG, notifier)
