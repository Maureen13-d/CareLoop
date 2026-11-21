from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_roles
from app.core.errors import DomainError
from app.modules.auth.models import ROLE_CHW, ROLE_CLINICIAN, ROLE_COUNSELLOR, ROLE_NAVIGATOR
from app.modules.tasks import service
from app.modules.tasks.models import NavigatorTask
from app.modules.tasks.schemas import TaskOut, TaskUpdate

router = APIRouter(prefix="/navigator/tasks", tags=["tasks"])
readers = require_roles(ROLE_NAVIGATOR, ROLE_COUNSELLOR, ROLE_CLINICIAN, ROLE_CHW)
staff = require_roles(ROLE_NAVIGATOR, ROLE_COUNSELLOR, ROLE_CLINICIAN)


@router.get("", response_model=list[TaskOut])
def list_tasks(
    status: str = Query("open", pattern="^(open|done|all)$"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(readers),
):
    stmt = select(NavigatorTask).order_by(NavigatorTask.id.desc())
    if status != "all":
        stmt = stmt.where(NavigatorTask.status == status)
    return [service.task_view(db, task) for task in db.scalars(stmt.limit(limit)).all()]


@router.patch("/{task_id}", response_model=TaskOut)
def patch_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    user=Depends(staff),
):
    task = db.get(NavigatorTask, task_id)
    if not task:
        raise DomainError(404, "not_found", "Task not found")
    service.complete_task(db, task, user, data.note)
    return service.task_view(db, task)
