from sqlalchemy.orm import Session

from app.core import clock
from app.modules.audit.models import AuditLog


def record(
    db: Session,
    *,
    actor,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    patient_id: int | None = None,
    detail: dict | None = None,
    outcome: str = "success",
    at=None,
) -> AuditLog:
    """Write one audit event. `actor` is a User, or None for the system.
    The caller commits, so an event is saved together with the change it describes."""
    entry = AuditLog(
        occurred_at=at or clock.now(),
        actor_id=actor.id if actor else None,
        actor_type="user" if actor else "system",
        role=actor.role if actor else "system",
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        patient_id=patient_id,
        detail=detail,
        outcome=outcome,
    )
    db.add(entry)
    return entry
