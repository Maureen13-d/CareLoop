"""Clip registry rows. Paths point at derived packs, never at raw footage."""

from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class KslSigner(Base):
    __tablename__ = "ksl_signers"

    id: Mapped[int] = mapped_column(primary_key=True)
    pseudonym: Mapped[str] = mapped_column(String(80), unique=True)
    consent_recorded_at: Mapped[datetime]
    consent_revoked_at: Mapped[datetime | None] = mapped_column(nullable=True)


class KslClip(Base):
    __tablename__ = "ksl_clips"

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[str] = mapped_column(String(80), index=True)
    source_text_hash: Mapped[str] = mapped_column(String(64))
    signer_id: Mapped[int] = mapped_column(ForeignKey("ksl_signers.id"))
    label: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(20), default="uploaded")
    pilot_enabled: Mapped[bool] = mapped_column(default=False)
    motion_uri: Mapped[str] = mapped_column(String(300))
    video_uri: Mapped[str | None] = mapped_column(String(300), nullable=True)
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime]
    approved_at: Mapped[datetime | None] = mapped_column(nullable=True)
    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class KslReview(Base):
    __tablename__ = "ksl_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    clip_id: Mapped[int] = mapped_column(ForeignKey("ksl_clips.id"), index=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str] = mapped_column(String(40))
    result: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime]


class KslFacilityFlag(Base):
    __tablename__ = "ksl_facility_flags"

    id: Mapped[int] = mapped_column(primary_key=True)
    facility_key: Mapped[str] = mapped_column(String(80), unique=True)
    interpreter_available: Mapped[bool] = mapped_column(default=False)
    recorded_on: Mapped[str] = mapped_column(String(10))
