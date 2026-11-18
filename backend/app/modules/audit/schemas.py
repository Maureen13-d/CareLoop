from pydantic import BaseModel, ConfigDict

from app.core.schemas import UtcDatetime


class AuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    occurred_at: UtcDatetime
    actor_id: int | None
    actor_type: str
    role: str | None
    action: str
    entity_type: str
    entity_id: int | None
    patient_id: int | None
    detail: dict | None
    outcome: str
