"""Outreach engine: decides who to contact, how, and when.

Design notes
- Pure planning logic (`plan_outreach`) is separate from side effects (`execute`).
- Privacy by design: messages never name the condition and carry no PHI.
- Channels are SIMULATED. Real SMS/voice needs real phone numbers (PHI), which
  docs/DATA_POLICY.md forbids. Swap in a real provider by implementing `Notifier`.
- Escalation ladder and cooldown values are PLACEHOLDERS pending clinical/operational review.
"""

from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models import Case
from app.pathway import SLA_DAYS, Stage, is_overdue


class Channel(str, Enum):
    SMS = "sms"
    CALL = "call"
    HOME_VISIT = "home_visit"  # community health worker visit
    COORDINATOR = "coordinator"  # hand-off to a human care coordinator


class Kind(str, Enum):
    REMINDER = "reminder"
    ESCALATION = "escalation"


LADDER: tuple[Channel, ...] = (Channel.SMS, Channel.CALL, Channel.HOME_VISIT)
COOLDOWN_DAYS = 3

# Deliberately neutral wording: never mention the condition, the test, or the result.
MESSAGES: dict[Stage, str] = {
    Stage.SCREENED: "A follow-up from your recent clinic visit is due. Please contact your clinic.",
    Stage.ABNORMAL_RESULT: (
        "Your clinic has a follow-up appointment for you. Please call or visit the clinic this week."
    ),
    Stage.REFERRED: (
        "Reminder: your referral appointment is still pending. "
        "Please attend or call the clinic to reschedule."
    ),
    Stage.DIAGNOSTIC_DONE: (
        "Your clinic has next steps to discuss with you. Please contact them to book a visit."
    ),
    Stage.TREATMENT_STARTED: "Please remember to attend your scheduled clinic visits.",
}
DEFAULT_MESSAGE = "Your clinic has a follow-up for you. Please get in touch."


class OutreachPlan(BaseModel):
    case_id: str
    patient_ref: str
    stage: Stage
    kind: Kind
    channel: Channel
    attempt: int
    message: str
    days_overdue: int


class OutreachEvent(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    case_id: str
    # Guardrail: same synthetic-only rule as Case. See docs/DATA_POLICY.md.
    patient_ref: str = Field(pattern=r"^SYN-\d{4,}$")
    stage: Stage
    kind: Kind
    channel: Channel
    attempt: int
    message: str
    status: str
    created_at: datetime


class Notifier(Protocol):
    def send(self, plan: OutreachPlan) -> str: ...


class SimulatedNotifier:
    """Sends nothing. Returns a status string so the pipeline can be demoed end to end."""

    def send(self, plan: OutreachPlan) -> str:
        return "simulated_delivered"


def _attempts_in_current_stage(case: Case, log: list[OutreachEvent]) -> list[OutreachEvent]:
    """Contacts made since the case entered its current stage (ladder resets on advance)."""
    events = [
        e
        for e in log
        if e.case_id == case.id and e.stage == case.stage and e.created_at >= case.stage_entered_at
    ]
    return sorted(events, key=lambda e: e.created_at)


def plan_outreach(
    case: Case, log: list[OutreachEvent], now: datetime | None = None
) -> OutreachPlan | None:
    """Return the next outreach action for a case, or None if nothing is due."""
    now = now or datetime.now(UTC)
    if case.stage == Stage.CLOSED or not is_overdue(case.stage, case.stage_entered_at, now):
        return None

    sent = _attempts_in_current_stage(case, log)
    if sent and now - sent[-1].created_at < timedelta(days=COOLDOWN_DAYS):
        return None  # cooling down

    n = len(sent)
    if n > len(LADDER):
        return None  # already escalated; a human owns this case now

    days_overdue = max((now - case.stage_entered_at).days - SLA_DAYS[case.stage], 0)
    if n == len(LADDER):
        return OutreachPlan(
            case_id=case.id,
            patient_ref=case.patient_ref,
            stage=case.stage,
            kind=Kind.ESCALATION,
            channel=Channel.COORDINATOR,
            attempt=n + 1,
            message=f"Care coordinator review needed: {n} outreach attempts without progress.",
            days_overdue=days_overdue,
        )
    return OutreachPlan(
        case_id=case.id,
        patient_ref=case.patient_ref,
        stage=case.stage,
        kind=Kind.REMINDER,
        channel=LADDER[n],
        attempt=n + 1,
        message=MESSAGES.get(case.stage, DEFAULT_MESSAGE),
        days_overdue=days_overdue,
    )


def execute(
    plan: OutreachPlan,
    log: list[OutreachEvent],
    notifier: Notifier,
    now: datetime | None = None,
) -> OutreachEvent:
    now = now or datetime.now(UTC)
    status = notifier.send(plan) if plan.kind == Kind.REMINDER else "queued_for_coordinator"
    event = OutreachEvent(
        case_id=plan.case_id,
        patient_ref=plan.patient_ref,
        stage=plan.stage,
        kind=plan.kind,
        channel=plan.channel,
        attempt=plan.attempt,
        message=plan.message,
        status=status,
        created_at=now,
    )
    log.append(event)
    return event


def run_sweep(
    cases: list[Case],
    log: list[OutreachEvent],
    notifier: Notifier,
    now: datetime | None = None,
) -> list[OutreachEvent]:
    now = now or datetime.now(UTC)
    created = []
    for case in cases:
        plan = plan_outreach(case, log, now)
        if plan is not None:
            created.append(execute(plan, log, notifier, now))
    return created
