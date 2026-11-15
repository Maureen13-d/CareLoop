from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.core.schemas import UtcDatetime


class CaseOut(BaseModel):
    id: int
    patient_id: int
    patient_ref: str | None
    patient_display_name: str | None
    pathway_id: str
    state: str
    state_label: str
    urgency: str
    owner_user_id: int | None
    owner_user_name: str | None
    owner_department: str | None
    unowned: bool
    state_entered_at: UtcDatetime
    deadline_at: UtcDatetime | None
    overdue: bool
    hours_overdue: float | None
    open_escalations: int
    opened_at: UtcDatetime
    closed_at: UtcDatetime | None
    closure_reason: str | None


class EventOut(BaseModel):
    id: int
    from_state: str | None
    to_state: str
    actor_type: str
    actor_name: str | None
    occurred_at: UtcDatetime
    note: str | None


class TransitionIn(BaseModel):
    to_state: str
    note: str | None = Field(default=None, max_length=500)


class EvidenceIn(BaseModel):
    type: str
    description: str = Field(min_length=1, max_length=1000)
    reference: str | None = Field(default=None, max_length=200)


class EvidenceOut(BaseModel):
    id: int
    case_id: int
    type: str
    description: str
    reference: str | None
    recorded_at: UtcDatetime


class CloseIn(BaseModel):
    evidence_type: str | None = None
    description: str | None = Field(default=None, max_length=1000)
    reference: str | None = Field(default=None, max_length=200)
    note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def description_needed_with_evidence(self):
        if self.evidence_type and not self.description:
            raise ValueError("description is required when evidence_type is given")
        return self


class LostIn(BaseModel):
    note: str = Field(min_length=1, max_length=500)


class EscalationOut(BaseModel):
    id: int
    case_id: int
    patient_ref: str | None
    state: str
    level: int
    reason: str
    raised_at: UtcDatetime
    resolved_at: UtcDatetime | None
    resolution_note: str | None


class ResolveIn(BaseModel):
    note: str = Field(min_length=1, max_length=500)


class PathwayStateOut(BaseModel):
    name: str
    label: str
    owner_department: str
    deadline_hours: int
    next: list[str]
    roles: list[str]


class PathwayOut(BaseModel):
    id: str
    name: str
    version: str
    deadlines_status: str
    initial_state: str
    states: list[PathwayStateOut]
    terminal_states: dict[str, str]


class AdvanceClockIn(BaseModel):
    hours: float = Field(gt=0, le=24 * 365)


class ClockOut(BaseModel):
    demo_now: UtcDatetime
    offset_hours: float


class DeadlineCheckOut(BaseModel):
    escalations_created: int
