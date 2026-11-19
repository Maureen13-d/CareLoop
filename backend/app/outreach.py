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
from app.pathway import SLA_DAYS, TRANSITIONS, InvalidTransition, Stage, is_overdue


class Channel(str, Enum):
    SMS = "sms"
    CALL = "call"
    HOME_VISIT = "home_visit"  # community health worker visit
    COORDINATOR = "coordinator"  # hand-off to a human care coordinator
    CLINIC = "clinic"  # patient attended in person


class Kind(str, Enum):
    REMINDER = "reminder"
    ESCALATION = "escalation"
    RESPONSE = "response"  # patient attended; this is what closes the loop


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


class CaseStatus(str, Enum):
    ON_TRACK = "on_track"
    OVERDUE = "overdue"
    ESCALATED = "escalated"
    CLOSED = "closed"


class AmbiguousTarget(ValueError):
    """The case has several valid next stages and the caller did not choose one."""


def next_stages(case: Case) -> list[Stage]:
    order = list(Stage)
    return sorted(TRANSITIONS[case.stage], key=order.index)


def case_status(case: Case, log: list[OutreachEvent], now: datetime | None = None) -> CaseStatus:
    now = now or datetime.now(UTC)
    if case.stage == Stage.CLOSED:
        return CaseStatus.CLOSED
    if not is_overdue(case.stage, case.stage_entered_at, now):
        return CaseStatus.ON_TRACK
    escalated = any(e.kind == Kind.ESCALATION for e in _attempts_in_current_stage(case, log))
    return CaseStatus.ESCALATED if escalated else CaseStatus.OVERDUE


def record_response(
    case: Case,
    log: list[OutreachEvent],
    to_stage: Stage | None = None,
    now: datetime | None = None,
) -> OutreachEvent:
    """The patient attended. Advance the case and log it, which closes the loop.

    The ladder resets automatically: contacts are scoped to (stage, stage_entered_at), and
    advancing changes both. The response event carries the stage the patient was in, so it
    never counts toward the next stage's ladder.
    """
    now = now or datetime.now(UTC)
    options = next_stages(case)
    if not options:
        raise InvalidTransition("Case is already closed")
    if to_stage is None:
        if len(options) > 1:
            choices = ", ".join(s.value for s in options)
            raise AmbiguousTarget(f"Several next stages are possible; choose one of: {choices}")
        to_stage = options[0]

    from_stage = case.stage
    contacts = len(_attempts_in_current_stage(case, log))  # before the stage changes
    case.advance(to_stage, now)  # raises InvalidTransition and leaves the case untouched

    event = OutreachEvent(
        case_id=case.id,
        patient_ref=case.patient_ref,
        stage=from_stage,
        kind=Kind.RESPONSE,
        channel=Channel.CLINIC,
        attempt=contacts,  # 0 means the patient attended without any outreach
        message=f"Patient attended. Case moved from {from_stage.value} to {to_stage.value}.",
        status="stage_advanced",
        created_at=now,
    )
    log.append(event)
    return event
