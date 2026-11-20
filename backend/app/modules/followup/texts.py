"""Approved lines. English and Swahili. No generation."""

from functools import lru_cache
from pathlib import Path

import yaml

from app.core.config import REPO_ROOT

TEMPLATES = Path(REPO_ROOT) / "ai" / "templates" / "followup.yaml"
LEXICON = Path(REPO_ROOT) / "ai" / "lexicon" / "followup_signs.yaml"
CHECKINS = Path(REPO_ROOT) / "config" / "followup_checkins.yaml"
WORKLIST = Path(REPO_ROOT) / "config" / "followup_worklist.yaml"


@lru_cache(maxsize=1)
def templates() -> dict:
    with open(TEMPLATES, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@lru_cache(maxsize=1)
def lexicon() -> dict:
    with open(LEXICON, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@lru_cache(maxsize=1)
def checkin_rules() -> dict:
    with open(CHECKINS, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@lru_cache(maxsize=1)
def worklist_rules() -> dict:
    with open(WORKLIST, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def line(key: str, language: str) -> str:
    pack = templates().get(language) or templates()["en"]
    return pack.get(key) or templates()["en"][key]


def slip_lines(language: str) -> list[str]:
    return [line("slip_1", language), line("slip_2", language), line("slip_3", language)]


def fit(text: str, channel: str) -> str:
    if channel == "sms":
        ascii_text = "".join(char if ord(char) < 128 else "" for char in text)
        return ascii_text[:160]
    if channel == "ussd":
        return text[:182]
    return text
