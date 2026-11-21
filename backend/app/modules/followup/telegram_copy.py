"""Approved Telegram strings and menus. No clinical rules live here."""

from functools import lru_cache
from pathlib import Path

import yaml

from app.core.config import REPO_ROOT

TEMPLATES = Path(REPO_ROOT) / "config" / "templates"
FLOWS = Path(REPO_ROOT) / "config" / "telegram_flows.yaml"
CLINICS = Path(REPO_ROOT) / "config" / "telegram_clinics.yaml"


@lru_cache(maxsize=1)
def flows() -> dict:
    with open(FLOWS, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@lru_cache(maxsize=1)
def clinics() -> dict:
    with open(CLINICS, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@lru_cache(maxsize=4)
def pack(language: str) -> dict:
    path = TEMPLATES / f"telegram.{language}.yaml"
    if not path.exists():
        path = TEMPLATES / "telegram.en.yaml"
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def line(key: str, language: str, **fmt) -> str:
    strings = pack(language).get("strings") or {}
    if key not in strings:
        strings = pack("en")["strings"]
    text = str(strings[key])
    if fmt:
        text = text.format(**fmt)
    return text


def all_strings() -> list[tuple[str, str, str]]:
    rows = []
    for language in ("en", "sw"):
        data = pack(language)
        for key, text in (data.get("strings") or {}).items():
            rows.append((language, key, str(text)))
        for menu in flows().values():
            if not isinstance(menu, dict):
                continue
            for row in menu.get("rows") or []:
                for button in row:
                    rows.append((language, "button", str(button.get("text", ""))))
    return rows


def button_rows(menu: str, *, inline: bool) -> list[list[dict]]:
    spec = flows()[menu]
    rows = []
    for row in spec.get("rows") or []:
        built = []
        for button in row:
            if inline:
                item = {"label": button["text"], "data": str(button.get("data") or button.get("action"))}
                if button.get("url"):
                    item["url"] = button["url"]
                built.append(item)
            else:
                built.append({"label": button["text"], "data": str(button.get("action") or button.get("data"))})
        rows.append(built)
    return rows


def label_map() -> dict[str, str]:
    found = {}
    for menu in flows().values():
        if not isinstance(menu, dict):
            continue
        for row in menu.get("rows") or []:
            for button in row:
                code = str(button.get("action") or button.get("data") or "")
                found[button["text"].strip().lower()] = code
    return found
