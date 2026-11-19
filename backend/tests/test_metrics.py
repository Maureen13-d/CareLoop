from datetime import UTC, datetime, timedelta

import pytest

from app.metrics import compute_metrics
from app.models import Case, StageEvent
from app.outreach import Channel, Kind, OutreachEvent
from app.pathway import Stage

NOW = datetime(2026, 6, 1, tzinfo=UTC)
R, ESC, RESP = Kind.REMINDER, Kind.ESCALATION, Kind.RESPONSE


def make_case(cid, n, path):
    history = [StageEvent(stage=s, at=NOW - timedelta(days=d)) for s, d in path]
    last = history[-1]
    return Case(
        id=cid,
        patient_ref=f"SYN-{1000 + n}",
        stage=last.stage,
        stage_entered_at=last.at,
        history=history,
    )


def ev(case, stage, kind, channel, attempt, days_ago):
    return OutreachEvent(
        case_id=case.id,
        patient_ref=case.patient_ref,
        stage=stage,
        kind=kind,
        channel=channel,
        attempt=attempt,
        message="x",
        status="ok",
        created_at=NOW - timedelta(days=days_ago),
    )


def scenario():
    S = Stage
    a = make_case("A", 1, [(S.SCREENED, 40), (S.ABNORMAL_RESULT, 30), (S.REFERRED, 20)])
    b = make_case("B", 2, [(S.SCREENED, 70), (S.ABNORMAL_RESULT, 60), (S.REFERRED, 50)])
    c = make_case(
        "C",
        3,
        [(S.SCREENED, 90), (S.ABNORMAL_RESULT, 85), (S.REFERRED, 80), (S.DIAGNOSTIC_DONE, 2)],
    )
    d = make_case("D", 4, [(S.SCREENED, 20)])
    e = make_case("E", 5, [(S.SCREENED, 1)])
    f = make_case("F", 6, [(S.SCREENED, 50), (S.ABNORMAL_RESULT, 40), (S.REFERRED, 30)])
    g = make_case("G", 7, [(S.SCREENED, 30), (S.ABNORMAL_RESULT, 12)])
    log = [
        # A: SMS, call, then attended
        ev(a, S.ABNORMAL_RESULT, R, Channel.SMS, 1, 25),
        ev(a, S.ABNORMAL_RESULT, R, Channel.CALL, 2, 22),
        ev(a, S.ABNORMAL_RESULT, RESP, Channel.CLINIC, 2, 20),
        # B: full ladder, escalated, still waiting
        ev(b, S.REFERRED, R, Channel.SMS, 1, 15),
        ev(b, S.REFERRED, R, Channel.CALL, 2, 12),
        ev(b, S.REFERRED, R, Channel.HOME_VISIT, 3, 9),
        ev(b, S.REFERRED, ESC, Channel.COORDINATOR, 4, 6),
        # C: full ladder, escalated, then attended
        ev(c, S.REFERRED, R, Channel.SMS, 1, 60),
        ev(c, S.REFERRED, R, Channel.CALL, 2, 57),
        ev(c, S.REFERRED, R, Channel.HOME_VISIT, 3, 54),
        ev(c, S.REFERRED, ESC, Channel.COORDINATOR, 4, 51),
        ev(c, S.REFERRED, RESP, Channel.CLINIC, 4, 2),
        # D: one SMS, still open
        ev(d, S.SCREENED, R, Channel.SMS, 1, 3),
        # F: contacted, then moved on with NO response event (the data-quality case)
        ev(f, S.ABNORMAL_RESULT, R, Channel.SMS, 1, 35),
    ]
    return [a, b, c, d, e, f, g], log


def test_loop_closure_numbers():
    cases, log = scenario()
    lc = compute_metrics(cases, log, NOW).loop_closure
    assert lc.contacted_episodes == 5  # A, B, C, D, F (E was never contacted)
    assert lc.attended == 2  # A, C
    assert lc.still_open == 2  # B, D
    assert lc.unrecorded_advances == 1  # F
    assert lc.closure_rate == 0.4
    assert lc.median_contacts_to_attend == 3.0  # median of 2 and 4
    assert lc.attended_by_last_channel == {
        "sms": 0,
        "call": 1,
        "home_visit": 0,
        "coordinator": 1,
    }


def test_escalation_numbers():
    cases, log = scenario()
    esc = compute_metrics(cases, log, NOW).escalation
    assert esc.escalated == 2  # B, C
    assert esc.escalation_rate == 0.4
    assert esc.recovered == 1  # C
    assert esc.recovery_rate == 0.5
    assert esc.awaiting_coordinator == 1  # B


def test_time_to_referral_numbers():
    cases, log = scenario()
    ttr = compute_metrics(cases, log, NOW).time_to_referral
    assert ttr.completed == 4  # A, B, C, F reached "referred"
    assert ttr.median_days == 10.0
    assert ttr.mean_days == pytest.approx(8.75, abs=0.1)
    assert ttr.within_sla_rate == 0.25  # only C (5 days) met the 7-day placeholder target
    assert ttr.sla_days == 7
    assert (ttr.awaiting, ttr.awaiting_overdue) == (1, 1)  # G is waiting, 12 days > 7


def test_total_cases_counts_everyone():
    cases, log = scenario()
    assert compute_metrics(cases, log, NOW).total_cases == 7


def test_empty_data_has_no_division_by_zero():
    m = compute_metrics([], [], NOW)
    assert m.loop_closure.closure_rate is None
    assert m.loop_closure.median_contacts_to_attend is None
    assert m.escalation.escalation_rate is None and m.escalation.recovery_rate is None
    assert m.time_to_referral.median_days is None
    assert m.time_to_referral.within_sla_rate is None


def test_attended_without_outreach_is_not_an_episode():
    case = make_case("X", 9, [(Stage.SCREENED, 10), (Stage.ABNORMAL_RESULT, 1)])
    log = [ev(case, Stage.SCREENED, RESP, Channel.CLINIC, 0, 1)]
    m = compute_metrics([case], log, NOW)
    assert m.loop_closure.attended_without_outreach == 1
    assert m.loop_closure.contacted_episodes == 0
    assert m.loop_closure.closure_rate is None


def test_disclaimer_says_synthetic():
    assert "synthetic" in compute_metrics([], [], NOW).disclaimer.lower()
