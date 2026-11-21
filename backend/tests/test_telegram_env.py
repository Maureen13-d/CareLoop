"""Credential lookup. Uses stand-in values only."""

from pathlib import Path

from app.modules.followup.telegram_env import setting


def test_canonical_name_wins_over_the_alias(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "canonical-token")
    monkeypatch.setenv("CARELOOP_TELEGRAM_BOT_TOKEN", "alias-token")
    assert setting("token", dotenv_path=Path("missing.env")) == "canonical-token"


def test_empty_canonical_name_does_not_fall_through(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "")
    monkeypatch.setenv("CARELOOP_TELEGRAM_WEBHOOK_SECRET", "alias-secret")
    assert setting("webhook_secret", dotenv_path=Path("missing.env")) == ""


def test_file_is_used_only_when_the_environment_is_silent(tmp_path, monkeypatch):
    for name in (
        "TELEGRAM_BOT_USERNAME",
        "CARELOOP_TELEGRAM_BOT_USERNAME",
        "PUBLIC_BASE_URL",
        "CARELOOP_PUBLIC_BASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)
    path = tmp_path / ".env"
    path.write_text(
        "CARELOOP_TELEGRAM_BOT_USERNAME=old-name\nTELEGRAM_BOT_USERNAME=loopie\n",
        encoding="utf-8",
    )
    assert setting("username", dotenv_path=path) == "loopie"
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("CARELOOP_TELEGRAM_BOT_TOKEN", raising=False)
    assert setting("token", dotenv_path=tmp_path / "missing.env") == ""
