from datetime import UTC, datetime, timedelta

import pytest

from app.models import Case, StageEvent
from app.outreach import (
    COOLDOWN_DAYS,
    AmbiguousTarget,
    CaseStatus,
    Channel,
    Kind,
    SimulatedNotifier,
    case_status,
    execute,
    plan_outreach,
    record_response,
)
from app.pathway import InvalidTransition, Stage

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


def _contact(case, log, now):
    plan = plan_outreach(case, log, now)
    assert plan is not None
    execute(plan, log, notifier, now)


def test_response_advances_stage_and_logs_event():
    case, log = make_case(), []
    event = record_response(case, log, now=NOW)
    assert case.stage == Stage.REFERRED
    assert case.stage_entered_at == NOW
    assert case.history[-1].stage == Stage.REFERRED
    assert (event.kind, event.channel, event.stage) == (
        Kind.RESPONSE,
        Channel.CLINIC,
        Stage.ABNORMAL_RESULT,
    )
    assert event.attempt == 0  # no outreach happened before the patient came in
    assert event.patient_ref.startswith("SYN-")
    assert log == [event]


def test_overdue_case_becomes_on_track():
    case, log = make_case(), []
    assert case_status(case, log, NOW) == CaseStatus.OVERDUE
    record_response(case, log, now=NOW)
    assert case_status(case, log, NOW) == CaseStatus.ON_TRACK


def test_escalated_case_recovers_and_records_attempts():
    case, log, now = make_case(), [], NOW
    for _ in range(4):  # three reminders + the escalation
        _contact(case, log, now)
        now += timedelta(days=COOLDOWN_DAYS)
    assert case_status(case, log, now) == CaseStatus.ESCALATED
    event = record_response(case, log, now=now)
    assert event.attempt == 4
    assert case_status(case, log, now) == CaseStatus.ON_TRACK


def test_ladder_restarts_in_the_next_stage():
    case, log, now = make_case(), [], NOW
    for _ in range(2):
        _contact(case, log, now)
        now += timedelta(days=COOLDOWN_DAYS)
    record_response(case, log, now=now)  # now REFERRED (30-day placeholder SLA)
    plan = plan_outreach(case, log, now + timedelta(days=31))
    assert plan is not None
    assert (plan.attempt, plan.channel) == (1, Channel.SMS)


def test_branching_stage_requires_an_explicit_outcome():
    case = make_case(stage=Stage.SCREENED, days_in_stage=20)
    with pytest.raises(AmbiguousTarget):
        record_response(case, [], now=NOW)
    assert case.stage == Stage.SCREENED  # nothing changed
    record_response(case, [], to_stage=Stage.CLOSED, now=NOW)
    assert case.stage == Stage.CLOSED
    assert case_status(case, [], NOW) == CaseStatus.CLOSED


def test_invalid_target_is_rejected_without_side_effects():
    case, log = make_case(), []
    with pytest.raises(InvalidTransition):
        record_response(case, log, to_stage=Stage.TREATMENT_STARTED, now=NOW)
    assert case.stage == Stage.ABNORMAL_RESULT
    assert log == []


def test_closed_case_cannot_respond():
    with pytest.raises(InvalidTransition):
        record_response(make_case(stage=Stage.CLOSED), [], now=NOW)
