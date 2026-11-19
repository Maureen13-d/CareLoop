from typing import Literal

from pydantic import BaseModel, Field

from app.core.schemas import UtcDatetime


class TaskOut(BaseModel):
    id: int
    case_id: int | None
    patient_ref: str | None
    patient_display_name: str | None
    task_type: str
    priority: str
    title: str
    summary: str
    status: str
    source: str
    created_at: UtcDatetime


class TaskUpdate(BaseModel):
    status: Literal["done"] = "done"
    note: str | None = Field(default=None, max_length=300)
