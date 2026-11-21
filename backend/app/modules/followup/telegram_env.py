"""Telegram credentials. Read from the environment. Never log the values."""

import os
from pathlib import Path

from app.core.config import BACKEND_DIR

# The first name is the one we document. The second keeps older deploys working.
ALIASES = {
    "token": ("TELEGRAM_BOT_TOKEN", "CARELOOP_TELEGRAM_BOT_TOKEN"),
    "webhook_secret": ("TELEGRAM_WEBHOOK_SECRET", "CARELOOP_TELEGRAM_WEBHOOK_SECRET"),
    "username": ("TELEGRAM_BOT_USERNAME", "CARELOOP_TELEGRAM_BOT_USERNAME"),
    "public_base_url": ("PUBLIC_BASE_URL", "CARELOOP_PUBLIC_BASE_URL"),
}


def _file_values(path: Path) -> dict[str, str]:
    found: dict[str, str] = {}
    if not path.is_file():
        return found
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, raw = line.partition("=")
        found[key.strip()] = raw.strip().strip('"').strip("'")
    return found


def present(kind: str, dotenv_path: Path | None = None) -> str:
    """First non-empty value. A blank name does not hide a later alias.

    When the process already has the names set, an empty value means "not
    configured" and the developer .env file is not opened.
    """
    seen = False
    for name in ALIASES[kind]:
        if name in os.environ:
            seen = True
            value = os.environ[name].strip()
            if value:
                return value
    if seen and dotenv_path is None:
        return ""
    path = BACKEND_DIR / ".env" if dotenv_path is None else dotenv_path
    file_values = _file_values(path)
    for name in ALIASES[kind]:
        value = file_values.get(name, "").strip()
        if value:
            return value
    return ""


def setting(kind: str, dotenv_path: Path | None = None) -> str:
    """An explicit environment value wins, including an empty string."""
    for name in ALIASES[kind]:
        if name in os.environ:
            return os.environ[name].strip()
    path = BACKEND_DIR / ".env" if dotenv_path is None else dotenv_path
    file_values = _file_values(path)
    for name in ALIASES[kind]:
        if name in file_values:
            return file_values[name].strip()
    return ""
