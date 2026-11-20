"""Deterministic maternal triage. No model. Thresholds live in rules/maternal_triage.yaml.

Output is decision support for a person. It is not a diagnosis.
PENDING CLINICAL REVIEW.
"""

from datetime import datetime, timedelta
from functools import lru_cache

import yaml

from app.core.config import REPO_ROOT

BANNED_SMS = (
    "pregnant",
    "pregnancy",
    "antenatal",
    "baby",
    "labour",
    "labor",
    "bp",
    "pre-eclampsia",
    "preeclampsia",
    "cancer",
    "result",
    "diagnosis",
    "positive",
    "hiv",
    "screening",
)

SMS_TEXT = {
    "red": "Please go to the nearest clinic now. A person will contact you.",
    "yellow": "A navigator can call you about your check. Reply 1 if you want a call.",
    "green": "Thanks. Next check-in is on the usual day. Reply HELP anytime.",
}


@lru_cache(maxsize=1)
def load_rules() -> dict:
    path = REPO_ROOT / "rules" / "maternal_triage.yaml"
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def reload_rules() -> dict:
    load_rules.cache_clear()
    return load_rules()


def _number(value) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _present(reading: dict, key: str, rules: dict) -> bool:
    value = reading.get(key)
    if key in {"systolic", "diastolic"}:
        return _number(value) is not None
    if key == "urine_protein":
        return isinstance(value, str) and value in rules["urine_rank"]
    if key == "hb_band":
        known = set(rules["hb_red"] + rules["hb_yellow"] + rules["hb_in_range"])
        return isinstance(value, str) and value in known
    return value not in (None, "")


def triage_maternal(reading: dict | None, danger_signs: list | None, context: dict | None = None) -> dict:
    """Return level, rule ids, reason labels, and the rules version.

    Missing or unreadable measurements never return green.
    """
    rules = load_rules()
    reading = reading or {}
    signs = [s for s in (danger_signs or []) if isinstance(s, str) and s]
    context = context or {}
    limits = rules["thresholds"]
    fired: list[str] = []
    reasons: list[str] = []

    def add(rule_id: str, reason: str) -> None:
        if rule_id not in fired:
            fired.append(rule_id)
            reasons.append(reason)

    if context.get("sos"):
        add("SOS", "SOS")

    for sign in signs:
        if sign in rules["red_signs"]:
            add("RED_SIGN", sign)
    if "headache_severe" in signs and "vision_blurred" in signs:
        add("NEURO_PAIR", "headache_with_vision")

    sys = _number(reading.get("systolic"))
    dia = _number(reading.get("diastolic"))
    severe = (sys is not None and sys >= limits["severe_systolic"]) or (
        dia is not None and dia >= limits["severe_diastolic"]
    )
    high = (sys is not None and sys >= limits["high_systolic"]) or (
        dia is not None and dia >= limits["high_diastolic"]
    )
    if severe:
        add("SEVERE_BP", "SEVERE_BP")

    urine = reading.get("urine_protein")
    rank = rules["urine_rank"].get(urine) if isinstance(urine, str) else None
    neuro = any(sign in rules["neuro_signs"] for sign in signs)
    if high and rank is not None and rank >= rules["urine_rank"]["2+"]:
        add("HIGH_BP_PROTEIN", "HIGH_BP_WITH_PROTEIN")
    if high and neuro:
        add("HIGH_BP_NEURO", "HIGH_BP_WITH_NEURO")

    hb = reading.get("hb_band")
    if hb in rules["hb_red"]:
        add("SEVERE_HB", "SEVERE_HB")

    red = any(
        rule in fired
        for rule in ("SOS", "RED_SIGN", "NEURO_PAIR", "SEVERE_BP", "HIGH_BP_PROTEIN", "HIGH_BP_NEURO", "SEVERE_HB")
    )

    if high and not severe:
        add("HIGH_BP", "HIGH_BP")
    if rank is not None and rank >= rules["urine_rank"]["1+"] and not high:
        add("PROTEIN", "PROTEIN")
    if hb in rules["hb_yellow"]:
        add("MODERATE_HB", "MODERATE_HB")
    for sign in signs:
        if sign in rules["yellow_signs"]:
            add("YELLOW_SIGN", sign)
    if context.get("missed_visit"):
        add("MISSED_VISIT", "MISSED_VISIT")

    missing = [key for key in rules["key_measurements"] if not _present(reading, key, rules)]
    if missing:
        add("INCOMPLETE_DATA", "INCOMPLETE_DATA")
        if len(missing) >= 2:
            add("TWO_MISSING", "TWO_MISSING")

    taken = reading.get("taken_at")
    now = context.get("now")
    gestation = context.get("gestation_band") or reading.get("gestation_band")
    if isinstance(taken, datetime) and isinstance(now, datetime):
        age = now - taken
        if (
            gestation in rules["gestation_past_20"]
            and age > timedelta(days=limits["stale_days"])
        ):
            add("STALE_READING", "STALE_READING")

    yellow_ids = {
        "HIGH_BP",
        "PROTEIN",
        "MODERATE_HB",
        "YELLOW_SIGN",
        "MISSED_VISIT",
        "INCOMPLETE_DATA",
        "TWO_MISSING",
        "STALE_READING",
    }
    yellow = any(rule in yellow_ids for rule in fired)

    if (
        rules.get("prior_yellow_escalates")
        and context.get("prior_level") == "yellow"
        and (yellow or signs)
        and not red
    ):
        add("PRIOR_YELLOW", "PRIOR_YELLOW")
        red = True

    if red:
        level = "red"
    elif yellow or missing:
        level = "yellow"
    else:
        in_range = (
            sys is not None
            and dia is not None
            and sys < limits["high_systolic"]
            and dia < limits["high_diastolic"]
            and rank is not None
            and rank <= rules["urine_rank"]["trace"]
            and hb in rules["hb_in_range"]
            and not signs
            and not context.get("sos")
            and not context.get("missed_visit")
        )
        level = "green" if in_range else "yellow"
        if level == "green":
            add("IN_RANGE", "IN_RANGE")
        elif "INCOMPLETE_DATA" not in fired:
            add("INCOMPLETE_DATA", "INCOMPLETE_DATA")

    return {
        "level": level,
        "rule_ids": fired,
        "reasons": reasons,
        "rules_version": rules["rules_version"],
    }


def render_sms(level: str) -> str:
    """Short discreet text. Never names a finding."""
    return SMS_TEXT.get(level, SMS_TEXT["yellow"])
