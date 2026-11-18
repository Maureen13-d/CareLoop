"""Care-pathway state machine. SLA values are PLACEHOLDERS pending clinical review."""
from datetime import UTC, datetime, timedelta
from enum import Enum


class Stage(str, Enum):
    SCREENED = "screened"
    ABNORMAL_RESULT = "abnormal_result"
    REFERRED = "referred"
    DIAGNOSTIC_DONE = "diagnostic_done"
    TREATMENT_STARTED = "treatment_started"
    CLOSED = "closed"


TRANSITIONS: dict[Stage, set[Stage]] = {
    Stage.SCREENED: {Stage.ABNORMAL_RESULT, Stage.CLOSED},  # normal result closes the case
    Stage.ABNORMAL_RESULT: {Stage.REFERRED},
    Stage.REFERRED: {Stage.DIAGNOSTIC_DONE},
    Stage.DIAGNOSTIC_DONE: {Stage.TREATMENT_STARTED, Stage.CLOSED},
    Stage.TREATMENT_STARTED: {Stage.CLOSED},
    Stage.CLOSED: set(),
}

# Max days a case may sit in a stage before it is flagged overdue (placeholders).
SLA_DAYS: dict[Stage, int] = {
    Stage.SCREENED: 14,
    Stage.ABNORMAL_RESULT: 7,
    Stage.REFERRED: 30,
    Stage.DIAGNOSTIC_DONE: 14,
    Stage.TREATMENT_STARTED: 90,
}


class InvalidTransition(ValueError):
    pass


def can_advance(current: Stage, target: Stage) -> bool:
    return target in TRANSITIONS[current]


def is_overdue(stage: Stage, entered_at: datetime, now: datetime | None = None) -> bool:
    sla = SLA_DAYS.get(stage)
    if sla is None:
        return False
    now = now or datetime.now(UTC)
    return now - entered_at > timedelta(days=sla)
