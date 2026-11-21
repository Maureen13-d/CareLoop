"""Shared discreet-language check. Extends the existing banned list. Does not fork it."""

import re

from app.modules.maternal.triage import BANNED_SMS

EXTRA = ("hpv", "via", "cytology", "tuberculosis", "diabetes", "malaria", "syphilis", "tb")
BANNED = tuple(dict.fromkeys((*BANNED_SMS, *EXTRA)))
REASSURANCE = (
    "you are fine",
    "you're fine",
    "you are ok",
    "nothing to worry",
    "no problem",
    "hamna shida",
    "uko sawa",
)


def problems(text: str) -> list[str]:
    low = (text or "").lower()
    found = []
    for word in BANNED:
        if len(word) <= 3:
            if re.search(rf"\b{re.escape(word)}\b", low):
                found.append(word)
        elif word in low:
            found.append(word)
    for phrase in REASSURANCE:
        if phrase in low:
            found.append(phrase)
    return found
