"""Approved phrase list. A clip can point at one of these lines and nothing else."""

from functools import lru_cache
from pathlib import Path

import yaml

from app.core.config import REPO_ROOT
from app.modules.followup.texts import templates

PATH = Path(REPO_ROOT) / "config" / "ksl_phrase_manifest.yaml"


@lru_cache(maxsize=1)
def manifest() -> tuple[dict, ...]:
    with open(PATH, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return tuple(data["phrases"])


def phrase_by_id(template_id: str) -> dict | None:
    for item in manifest():
        if item["id"] == template_id:
            return item
    return None


def phrase_text(item: dict) -> str:
    if item.get("en"):
        return str(item["en"])
    return templates()["en"][item["id"]]


def current_caption(template_id: str) -> str | None:
    item = phrase_by_id(template_id)
    if item is not None:
        return phrase_text(item)
    pack = templates().get("en") or {}
    if template_id in pack:
        return pack[template_id]
    return None
