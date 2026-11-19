"""Grounded retrieval for web chat.

Picks one approved passage by phrase or word overlap. It never writes a new medical
claim: the reply is the passage text, and the caller shows the source. SMS and USSD
do not use this tier, so shared phones stay on the short approved templates.
"""

from functools import lru_cache
from pathlib import Path

import yaml

from app.core.config import settings
from app.modules.assistant.text import normalise, tokens

STOP = {
    "a",
    "an",
    "the",
    "to",
    "i",
    "my",
    "me",
    "is",
    "of",
    "for",
    "and",
    "what",
    "how",
    "can",
    "do",
    "does",
    "at",
    "on",
    "you",
    "your",
    "it",
    "this",
    "with",
    "be",
    "or",
    "if",
    "we",
    "in",
    "that",
    "are",
    "will",
    "about",
    "from",
    "have",
    "has",
}


@lru_cache(maxsize=1)
def load_passages() -> tuple[dict, ...]:
    path = Path(settings.ai_dir) / "knowledge" / "passages_en.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return tuple(data["passages"])


def search_passages(text: str) -> dict | None:
    """Return the best passage, or None when the question is not covered."""
    norm = normalise(text)
    content = [t for t in tokens(norm) if t not in STOP and len(t) > 2]
    best: dict | None = None
    best_score = 0
    for passage in load_passages():
        prompts = [normalise(p) for p in passage.get("prompts", [])]
        if any(len(prompt) >= 10 and (prompt in norm or norm in prompt) for prompt in prompts):
            score = 100
        else:
            hay = set(
                tokens(
                    normalise(
                        f"{passage['title']} {passage['text']} {' '.join(passage.get('prompts', []))}"
                    )
                )
            )
            score = sum(1 for word in content if word in hay)
        if score > best_score:
            best, best_score = passage, score
    if best is not None and best_score >= 3:
        return best
    return None
