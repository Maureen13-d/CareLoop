"""Tier 0: safety rules. Always run first, on every channel.

Deliberately broad: a false alarm costs a human a minute; a missed crisis costs far more.
Negation is NOT applied here ("I don't want to live" must not be cancelled by the "don't")."""
from app.modules.assistant.lexicon import load_safety
from app.modules.assistant.schemas import SafetyResult
from app.modules.assistant.text import phrase_positions, tokens

PRIORITY = ["crisis", "distress", "symptom_report", "diagnosis_request"]  # highest first


def check_safety(norm: str) -> SafetyResult:
    toks = tokens(norm)
    lex = load_safety()
    matched = [cat for cat in PRIORITY if any(phrase_positions(toks, p) for p in lex.categories[cat])]
    return SafetyResult(level=matched[0] if matched else "none", matched=matched)
