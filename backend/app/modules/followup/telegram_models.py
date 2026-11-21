"""Telegram contact vault and deep links. The chat id lives only on TelegramVault."""

from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TelegramVault(Base):
    """Chat link for one Patient ID. Clinical tables do not read this."""

    __tablename__ = "telegram_vault"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(20), unique=True)
    chat_id: Mapped[str | None] = mapped_column(String(40), unique=True, nullable=True)
    unreachable: Mapped[bool] = mapped_column(default=False)
    tips_opt_in: Mapped[bool] = mapped_column(default=False)
    celebrated: Mapped[bool] = mapped_column(default=False)
    pending_labels: Mapped[str] = mapped_column(String(80), default="")
    paused_until: Mapped[datetime | None] = mapped_column(nullable=True)


class TelegramDeepLink(Base):
    """Opaque single-use start token. It is not the Patient ID."""

    __tablename__ = "telegram_deeplinks"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True)
    public_id: Mapped[str] = mapped_column(String(20), index=True)
    expires_at: Mapped[datetime]
    used_at: Mapped[datetime | None] = mapped_column(nullable=True)


class TelegramChat(Base):
    """Onboarding flags keyed by a hash, never by the raw chat id."""

    __tablename__ = "telegram_chat_state"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_key: Mapped[str] = mapped_column(String(40), unique=True)
    group_noted: Mapped[bool] = mapped_column(default=False)
    pending_token: Mapped[str] = mapped_column(String(64), default="")
