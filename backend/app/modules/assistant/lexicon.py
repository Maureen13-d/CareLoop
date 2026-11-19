"""Loads the lexicons and templates from the repository's ai/ folder."""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from app.core.config import settings
from app.modules.assistant.text import normalise


def _read(relative: str) -> dict:
    with open(Path(settings.ai_dir) / relative, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _norm_list(items) -> tuple[str, ...]:
    return tuple(normalise(i) for i in (items or []))


@dataclass(frozen=True)
class Entry:
    phrases: tuple[str, ...]
    keywords: tuple[str, ...]
    exact: tuple[str, ...]


@dataclass(frozen=True)
class SafetyLexicon:
    version: str
    categories: dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class BarrierLexicon:
    version: str
    threshold: int
    phrase_weight: int
    keyword_weight: int
    negation_window: int
    flags: dict[str, Entry]
    intents: dict[str, Entry]
    worry_menu: dict[str, str]


@lru_cache(maxsize=1)
def load_safety() -> SafetyLexicon:
    data = _read("lexicon/safety_en.yaml")
    cats = {
        name: _norm_list(data[name]["phrases"])
        for name in ("crisis", "distress", "symptom_report", "diagnosis_request")
    }
    return SafetyLexicon(version=str(data["version"]), categories=cats)


def _entries(block: dict) -> dict[str, Entry]:
    return {
        name: Entry(
            _norm_list(e.get("phrases")), _norm_list(e.get("keywords")), _norm_list(e.get("exact"))
        )
        for name, e in (block or {}).items()
    }


@lru_cache(maxsize=1)
def load_barriers() -> BarrierLexicon:
    data = _read("lexicon/barriers_en.yaml")
    return BarrierLexicon(
        version=str(data["version"]),
        threshold=int(data["threshold"]),
        phrase_weight=int(data["phrase_weight"]),
        keyword_weight=int(data["keyword_weight"]),
        negation_window=int(data["negation_window"]),
        flags=_entries(data["flags"]),
        intents=_entries(data["intents"]),
        worry_menu={str(k): v for k, v in data["worry_menu"].items()},
    )


@lru_cache(maxsize=1)
def load_templates() -> dict[str, dict]:
    return _read("templates/lite_en.yaml")["templates"]


def get_template(template_id: str) -> dict:
    templates = load_templates()
    if template_id not in templates:
        raise KeyError(f"Unknown template: {template_id}")
    return templates[template_id]
