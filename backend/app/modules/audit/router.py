from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_roles
from app.modules.audit.models import AuditLog
from app.modules.audit.schemas import AuditOut
from app.modules.auth.models import ROLE_ADMIN, ROLE_PROGRAM_MANAGER

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditOut])
def list_audit(
    action: str | None = None,
    entity_type: str | None = None,
    outcome: str | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user=Depends(require_roles(ROLE_ADMIN, ROLE_PROGRAM_MANAGER)),
):
    stmt = select(AuditLog).order_by(AuditLog.id.desc())
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if outcome:
        stmt = stmt.where(AuditLog.outcome == outcome)
    return db.scalars(stmt.limit(limit).offset(offset)).all()
