"""Scripted demo data. Enabled with CARELOOP_DEMO_SCENARIO=true. Synthetic only."""

from datetime import UTC, datetime, timedelta

from app.models import Case, StageEvent
from app.outreach import MESSAGES, Channel, Kind, OutreachEvent
from app.pathway import Stage

DEMO_CASE_ID = "case-demo"
DEMO_PATIENT_REF = "SYN-9000"


def seed_demo_scenario(
    store: dict[str, Case], log: list[OutreachEvent], now: datetime | None = None
) -> None:
    """One case that fell through the cracks: referred 45 days ago, every automated contact
    already tried, escalated to a coordinator 5 days ago."""
    now = now or datetime.now(UTC)

    def ago(days: int) -> datetime:
        return now - timedelta(days=days)

    store[DEMO_CASE_ID] = Case(
        id=DEMO_CASE_ID,
        patient_ref=DEMO_PATIENT_REF,
        stage=Stage.REFERRED,
        stage_entered_at=ago(45),
        history=[
            StageEvent(stage=Stage.SCREENED, at=ago(60)),
            StageEvent(stage=Stage.ABNORMAL_RESULT, at=ago(53)),
            StageEvent(stage=Stage.REFERRED, at=ago(45)),
        ],
    )

    steps = [
        (14, Kind.REMINDER, Channel.SMS, "simulated_delivered"),
        (11, Kind.REMINDER, Channel.CALL, "simulated_delivered"),
        (8, Kind.REMINDER, Channel.HOME_VISIT, "simulated_delivered"),
        (5, Kind.ESCALATION, Channel.COORDINATOR, "queued_for_coordinator"),
    ]
    for attempt, (days_ago, kind, channel, status) in enumerate(steps, start=1):
        message = (
            MESSAGES[Stage.REFERRED]
            if kind == Kind.REMINDER
            else "Care coordinator review needed: 3 outreach attempts without progress."
        )
        log.append(
            OutreachEvent(
                case_id=DEMO_CASE_ID,
                patient_ref=DEMO_PATIENT_REF,
                stage=Stage.REFERRED,
                kind=kind,
                channel=channel,
                attempt=attempt,
                message=message,
                status=status,
                created_at=ago(days_ago),
            )
        )
