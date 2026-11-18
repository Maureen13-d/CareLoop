from datetime import UTC, datetime

from pydantic import BaseModel, Field

from app.pathway import InvalidTransition, Stage, can_advance


class StageEvent(BaseModel):
    stage: Stage
    at: datetime


class Case(BaseModel):
    id: str
    # Guardrail: only synthetic identifiers are accepted. See docs/DATA_POLICY.md.
    patient_ref: str = Field(pattern=r"^SYN-\d{4,}$")
    stage: Stage
    stage_entered_at: datetime
    history: list[StageEvent] = Field(default_factory=list)

    def advance(self, target: Stage, now: datetime | None = None) -> None:
        if not can_advance(self.stage, target):
            raise InvalidTransition(f"Cannot move from {self.stage.value} to {target.value}")
        now = now or datetime.now(UTC)
        self.stage = target
        self.stage_entered_at = now
        self.history.append(StageEvent(stage=target, at=now))


class CaseView(Case):
    overdue: bool


class AdvanceRequest(BaseModel):
    to_stage: Stage
