"""Tier 1: Lite mode. Keyword and phrase matching with approved replies. No model, no network.

Scoring: each distinct phrase matched adds phrase_weight, each distinct keyword adds keyword_weight.
A flag is raised at the threshold. Matches directly after a negation word ("not afraid") are ignored."""
from dataclasses import dataclass, field

from app.modules.assistant.lexicon import load_barriers
from app.modules.assistant.text import is_negated, phrase_positions, tokens


@dataclass
class LiteMatch:
    flags: list[tuple[str, int]] = field(default_factory=list)   # (flag, score), best first
    intents: list[str] = field(default_factory=list)

    @property
    def ambiguous(self) -> bool:
        return len(self.flags) >= 2 and self.flags[0][1] - self.flags[1][1] <= 1


def _score(toks: list[str], entry, lex) -> int:
    score = 0
    for phrase in entry.phrases:
        if any(not is_negated(toks, pos, lex.negation_window) for pos in phrase_positions(toks, phrase)):
            score += lex.phrase_weight
    for word in entry.keywords:
        if any(not is_negated(toks, pos, lex.negation_window) for pos in phrase_positions(toks, word)):
            score += lex.keyword_weight
    return score


def match_lite(norm: str) -> LiteMatch:
    lex = load_barriers()
    toks = tokens(norm)
    result = LiteMatch()

    for name, entry in lex.intents.items():
        exact_hit = norm in entry.exact
        phrase_hit = any(phrase_positions(toks, p) for p in entry.phrases)
        if exact_hit or phrase_hit:
            result.intents.append(name)

    scored = []
    for order, (name, entry) in enumerate(lex.flags.items()):
        score = _score(toks, entry, lex)
        if score >= lex.threshold:
            scored.append((name, score, order))
    scored.sort(key=lambda x: (-x[1], x[2]))
    result.flags = [(name, score) for name, score, _ in scored]
    return result


def confidence(score: int, lex=None) -> float:
    return round(min(1.0, score / 6), 2)
