"""Draft maternal passages. Searched only for a maternal request."""

from functools import lru_cache
from pathlib import Path

import yaml

from app.core.config import settings
from app.modules.assistant.retrieve import STOP
from app.modules.assistant.text import normalise, tokens


@lru_cache(maxsize=1)
def load_maternal_passages() -> tuple[dict, ...]:
    path = Path(settings.ai_dir) / "knowledge" / "passages_maternal.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return tuple(data["passages"])


def search_maternal(text: str) -> dict | None:
    norm = normalise(text)
    content = [word for word in tokens(norm) if word not in STOP and len(word) > 2]
    best: dict | None = None
    best_score = 0
    for passage in load_maternal_passages():
        prompts = [normalise(prompt) for prompt in passage.get("prompts", [])]
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
