"""Table tests for maternal triage. Thresholds are placeholders, not clinical guidance."""

from datetime import datetime, timedelta

import pytest

from app.modules.maternal.triage import BANNED_SMS, render_sms, triage_maternal

NOW = datetime(2026, 11, 20, 9, 0)
FRESH = NOW - timedelta(days=1)
OLD = NOW - timedelta(days=15)

GREEN = {
    "systolic": 118,
    "diastolic": 76,
    "urine_protein": "neg",
    "hb_band": "normal",
    "taken_at": FRESH,
    "gestation_band": "28-36w",
}


def case(name, reading, signs, context, level):
    return (name, reading, signs, context, level)


# Boundaries, combinations, missing data, and conflicts. Unknown never lands on green.
CASES = [
    case("green baseline", GREEN, [], {"now": NOW}, "green"),
    case("sys just below severe", {**GREEN, "systolic": 159}, [], {"now": NOW}, "yellow"),
    case("sys at severe", {**GREEN, "systolic": 160}, [], {"now": NOW}, "red"),
    case("sys above severe", {**GREEN, "systolic": 161}, [], {"now": NOW}, "red"),
    case("dia just below severe", {**GREEN, "diastolic": 109}, [], {"now": NOW}, "yellow"),
    case("dia at severe", {**GREEN, "diastolic": 110}, [], {"now": NOW}, "red"),
    case("dia above severe", {**GREEN, "diastolic": 111}, [], {"now": NOW}, "red"),
    case("sys just below high", {**GREEN, "systolic": 139}, [], {"now": NOW}, "green"),
    case("sys at high", {**GREEN, "systolic": 140}, [], {"now": NOW}, "yellow"),
    case("dia just below high", {**GREEN, "diastolic": 89}, [], {"now": NOW}, "green"),
    case("dia at high", {**GREEN, "diastolic": 90}, [], {"now": NOW}, "yellow"),
    case("urine trace is in range", {**GREEN, "urine_protein": "trace"}, [], {"now": NOW}, "green"),
    case("urine 1+ normal bp", {**GREEN, "urine_protein": "1+"}, [], {"now": NOW}, "yellow"),
    case("urine 2+ normal bp", {**GREEN, "urine_protein": "2+"}, [], {"now": NOW}, "yellow"),
    case("urine 3+ normal bp", {**GREEN, "urine_protein": "3+"}, [], {"now": NOW}, "yellow"),
    case(
        "urine 2+ with high bp",
        {**GREEN, "systolic": 140, "urine_protein": "2+"},
        [],
        {"now": NOW},
        "red",
    ),
    case(
        "urine 1+ with high bp stays yellow",
        {**GREEN, "systolic": 140, "urine_protein": "1+"},
        [],
        {"now": NOW},
        "yellow",
    ),
    case("hb mild in range", {**GREEN, "hb_band": "mild"}, [], {"now": NOW}, "green"),
    case("hb moderate", {**GREEN, "hb_band": "moderate"}, [], {"now": NOW}, "yellow"),
    case("hb severe", {**GREEN, "hb_band": "severe"}, [], {"now": NOW}, "red"),
    case("heavy bleeding", GREEN, ["heavy_bleeding"], {"now": NOW}, "red"),
    case("convulsion", GREEN, ["convulsion"], {"now": NOW}, "red"),
    case("abdominal pain", GREEN, ["severe_abdominal_pain"], {"now": NOW}, "red"),
    case("breathing", GREEN, ["difficulty_breathing"], {"now": NOW}, "red"),
    case("no movement", GREEN, ["no_fetal_movement"], {"now": NOW}, "red"),
    case("fever with weakness", GREEN, ["fever_severe_weakness"], {"now": NOW}, "red"),
    case("leaking with fever label", GREEN, ["leaking_fluid_fever"], {"now": NOW}, "red"),
    case("headache and vision", GREEN, ["headache_severe", "vision_blurred"], {"now": NOW}, "red"),
    case("headache alone", GREEN, ["headache_only"], {"now": NOW}, "yellow"),
    case("vision alone", GREEN, ["vision_blurred"], {"now": NOW}, "yellow"),
    case(
        "vision with high bp",
        {**GREEN, "systolic": 142},
        ["vision_blurred"],
        {"now": NOW},
        "red",
    ),
    case("swelling", GREEN, ["swelling_face_hands"], {"now": NOW}, "yellow"),
    case("reduced movement", GREEN, ["reduced_fetal_movement"], {"now": NOW}, "yellow"),
    case("missed visit flag", GREEN, ["missed_visit"], {"now": NOW}, "yellow"),
    case("missed visit context", GREEN, [], {"now": NOW, "missed_visit": True}, "yellow"),
    case("sos", GREEN, [], {"now": NOW, "sos": True}, "red"),
    case("blank reading", {}, [], {"now": NOW}, "yellow"),
    case("urine unknown", {**GREEN, "urine_protein": "unknown"}, [], {"now": NOW}, "yellow"),
    case("hb unknown", {**GREEN, "hb_band": "unknown"}, [], {"now": NOW}, "yellow"),
    case("sys unreadable", {**GREEN, "systolic": "high"}, [], {"now": NOW}, "yellow"),
    case("sys missing only", {**GREEN, "systolic": None}, [], {"now": NOW}, "yellow"),
    case(
        "two missing",
        {**GREEN, "systolic": None, "diastolic": None},
        [],
        {"now": NOW},
        "yellow",
    ),
    case(
        "stale after 20 weeks",
        {**GREEN, "taken_at": OLD},
        [],
        {"now": NOW},
        "yellow",
    ),
    case(
        "stale before 20 weeks",
        {**GREEN, "taken_at": OLD, "gestation_band": "<20w"},
        [],
        {"now": NOW, "gestation_band": "<20w"},
        "green",
    ),
    case(
        "stale at 14 days is not over",
        {**GREEN, "taken_at": NOW - timedelta(days=14)},
        [],
        {"now": NOW},
        "green",
    ),
    case(
        "prior yellow plus swelling",
        GREEN,
        ["swelling_face_hands"],
        {"now": NOW, "prior_level": "yellow"},
        "red",
    ),
    case(
        "prior yellow and a clean reading stays green",
        GREEN,
        [],
        {"now": NOW, "prior_level": "yellow"},
        "green",
    ),
    case(
        "severe bp beats a normal urine story",
        {**GREEN, "systolic": 170, "urine_protein": "neg"},
        [],
        {"now": NOW},
        "red",
    ),
    case("empty signs and none reading", None, None, None, "yellow"),
    case("bool systolic is unreadable", {**GREEN, "systolic": True}, [], {"now": NOW}, "yellow"),
]


def test_table_has_at_least_40_cases():
    assert len(CASES) >= 40


@pytest.mark.parametrize(("name", "reading", "signs", "context", "level"), CASES, ids=[c[0] for c in CASES])
def test_triage_level(name, reading, signs, context, level):
    result = triage_maternal(reading, signs, context)
    assert result["level"] == level, result
    assert result["rules_version"]
    assert result["reasons"]


def test_unknown_is_never_green():
    for urine in (None, "", "unknown", "plus", "++"):
        result = triage_maternal({**GREEN, "urine_protein": urine}, [], {"now": NOW})
        assert result["level"] != "green"


def test_sms_render_stays_discreet_and_short():
    for level in ("red", "yellow", "green"):
        text = render_sms(level)
        assert len(text) <= 160
        assert text.isascii()
        folded = text.lower()
        assert not any(word in folded for word in BANNED_SMS)
