"""Aggregate counts for the desk. No names, no message text."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.db import get_db
from app.core.deps import require_roles
from app.modules.auth.models import (
    ROLE_ADMIN,
    ROLE_CLINICIAN,
    ROLE_COUNSELLOR,
    ROLE_NAVIGATOR,
    ROLE_PROGRAM_MANAGER,
)
from app.modules.pathways.loader import load_pathway
from app.modules.pathways.models import CareCase, Escalation
from app.modules.tasks.models import NavigatorTask

router = APIRouter(prefix="/analytics", tags=["analytics"])
readers = require_roles(
    ROLE_NAVIGATOR, ROLE_CLINICIAN, ROLE_COUNSELLOR, ROLE_PROGRAM_MANAGER, ROLE_ADMIN
)


def _count(db: Session, pathway_id: str, *where) -> int:
    stmt = select(func.count()).select_from(CareCase).where(CareCase.pathway_id == pathway_id)
    for clause in where:
        stmt = stmt.where(clause)
    return int(db.scalar(stmt) or 0)


@router.get("/funnel")
def funnel(db: Session = Depends(get_db), _=Depends(readers)):
    pathway = load_pathway()
    stages = [
        {
            "state": name,
            "label": state.label,
            "count": _count(db, pathway.id, CareCase.state == name),
        }
        for name, state in pathway.states.items()
    ]
    terminals = [
        {"state": name, "label": label, "count": _count(db, pathway.id, CareCase.state == name)}
        for name, label in pathway.terminal_states.items()
    ]
    return {
        "pathway_id": pathway.id,
        "pathway_name": pathway.name,
        "deadlines_status": pathway.deadlines_status,
        "stages": stages,
        "terminals": terminals,
    }


@router.get("/summary")
def summary(db: Session = Depends(get_db), _=Depends(readers)):
    pathway = load_pathway()
    terminal = list(pathway.terminal_states)
    now = clock.now()
    open_cases = _count(db, pathway.id, CareCase.state.not_in(terminal))
    overdue = _count(
        db,
        pathway.id,
        CareCase.state.not_in(terminal),
        CareCase.deadline_at.is_not(None),
        CareCase.deadline_at < now,
    )
    unowned = _count(
        db, pathway.id, CareCase.state.not_in(terminal), CareCase.owner_user_id.is_(None)
    )
    open_escalations = int(
        db.scalar(
            select(func.count()).select_from(Escalation).where(Escalation.resolved_at.is_(None))
        )
        or 0
    )
    open_tasks = int(
        db.scalar(
            select(func.count()).select_from(NavigatorTask).where(NavigatorTask.status == "open")
        )
        or 0
    )
    return {
        "open_cases": open_cases,
        "overdue": overdue,
        "unowned": unowned,
        "open_escalations": open_escalations,
        "open_tasks": open_tasks,
        "handed_off": _count(db, pathway.id, CareCase.state == "HANDED_OFF"),
        "deadlines_status": pathway.deadlines_status,
    }
