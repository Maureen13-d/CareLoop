from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.models import Case, StageEvent
from app.outreach import (
    COOLDOWN_DAYS,
    MESSAGES,
    Channel,
    Kind,
    OutreachEvent,
    SimulatedNotifier,
    execute,
    plan_outreach,
    run_sweep,
)
from app.pathway import Stage

NOW = datetime(2026, 1, 1, tzinfo=UTC)
notifier = SimulatedNotifier()


def make_case(stage=Stage.ABNORMAL_RESULT, days_in_stage=10, cid="c1", ref="SYN-1234"):
    entered = NOW - timedelta(days=days_in_stage)
    return Case(
        id=cid,
        patient_ref=ref,
        stage=stage,
        stage_entered_at=entered,
        history=[StageEvent(stage=stage, at=entered)],
    )


def test_no_outreach_within_sla():
    assert plan_outreach(make_case(days_in_stage=3), [], NOW) is None


def test_no_outreach_for_closed_case():
    assert plan_outreach(make_case(stage=Stage.CLOSED, days_in_stage=500), [], NOW) is None


def test_first_plan_is_sms_attempt_one():
    plan = plan_outreach(make_case(), [], NOW)
    assert plan is not None
    assert (plan.kind, plan.channel, plan.attempt) == (Kind.REMINDER, Channel.SMS, 1)
    assert plan.days_overdue == 3  # 10 days in stage, 7-day placeholder SLA


def test_full_escalation_ladder_then_stops():
    case, log, now = make_case(), [], NOW
    expected = [
        (Kind.REMINDER, Channel.SMS),
        (Kind.REMINDER, Channel.CALL),
        (Kind.REMINDER, Channel.HOME_VISIT),
        (Kind.ESCALATION, Channel.COORDINATOR),
    ]
    for kind, channel in expected:
        plan = plan_outreach(case, log, now)
        assert plan is not None
        assert (plan.kind, plan.channel) == (kind, channel)
        execute(plan, log, notifier, now)
        now += timedelta(days=COOLDOWN_DAYS)
    assert plan_outreach(case, log, now) is None  # a human owns it now


def test_cooldown_blocks_repeat_contact():
    case, log = make_case(), []
    first = plan_outreach(case, log, NOW)
    assert first is not None
    execute(first, log, notifier, NOW)
    assert plan_outreach(case, log, NOW + timedelta(days=COOLDOWN_DAYS - 1)) is None
    assert plan_outreach(case, log, NOW + timedelta(days=COOLDOWN_DAYS)) is not None


def test_attempts_do_not_carry_over_between_stages():
    case = make_case(stage=Stage.REFERRED, days_in_stage=40)  # 30-day placeholder SLA
    old = OutreachEvent(
        case_id=case.id,
        patient_ref=case.patient_ref,
        stage=Stage.ABNORMAL_RESULT,
        kind=Kind.REMINDER,
        channel=Channel.SMS,
        attempt=1,
        message="x",
        status="simulated_delivered",
        created_at=NOW - timedelta(days=45),
    )
    plan = plan_outreach(case, [old], NOW)
    assert plan is not None
    assert (plan.attempt, plan.channel) == (1, Channel.SMS)


def test_sweep_is_idempotent_within_cooldown():
    cases = [make_case(cid="a"), make_case(cid="b", ref="SYN-1235", days_in_stage=1)]
    log = []
    first = run_sweep(cases, log, notifier, NOW)
    assert [e.case_id for e in first] == ["a"]
    assert run_sweep(cases, log, notifier, NOW) == []


def test_outreach_event_rejects_non_synthetic_ref():
    with pytest.raises(ValidationError):
        OutreachEvent(
            case_id="c1",
            patient_ref="MRN-12345",
            stage=Stage.SCREENED,
            kind=Kind.REMINDER,
            channel=Channel.SMS,
            attempt=1,
            message="x",
            status="simulated_delivered",
            created_at=NOW,
        )


BANNED = ("cancer", "cervical", "hpv", "positive", "abnormal", "screening")


def test_messages_do_not_disclose_condition():
    for stage, text in MESSAGES.items():
        assert not any(word in text.lower() for word in BANNED), stage
