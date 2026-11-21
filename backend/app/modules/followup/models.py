"""Follow-up rows. The contact lives only in the vault."""

from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Enrolment(Base):
    __tablename__ = "followup_enrolments"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    public_id: Mapped[str] = mapped_column(String(20), unique=True)
    case_id: Mapped[int | None] = mapped_column(ForeignKey("care_cases.id"), nullable=True)
    screening_type: Mapped[str] = mapped_column(String(40))
    finding: Mapped[str] = mapped_column(String(20))
    language: Mapped[str] = mapped_column(String(8), default="en")
    channel: Mapped[str] = mapped_column(String(16), default="web")
    area_label: Mapped[str] = mapped_column(String(40))
    assigned_chw_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    symptom_flag: Mapped[str] = mapped_column(String(16), default="none")
    missed_replies: Mapped[int] = mapped_column(default=0)
    checkin_attempts: Mapped[int] = mapped_column(default=0)
    messages_stopped: Mapped[bool] = mapped_column(default=False)
    barrier_label: Mapped[str | None] = mapped_column(String(40), nullable=True)
    reported_visit: Mapped[bool] = mapped_column(default=False)
    last_checkin_at: Mapped[datetime | None] = mapped_column(nullable=True)
    window_open_until: Mapped[datetime | None] = mapped_column(nullable=True)
    opened_at: Mapped[datetime]


class ContactVault(Base):
    """Personal contact. Dashboards do not read this table."""

    __tablename__ = "contact_vault"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(20), unique=True)
    contact_ref: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime]


class AccessCode(Base):
    __tablename__ = "followup_access_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(20), index=True)
    code_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime]
    used_at: Mapped[datetime | None] = mapped_column(nullable=True)


class ChannelSession(Base):
    __tablename__ = "followup_sessions"
    __table_args__ = (UniqueConstraint("channel", "session_key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    channel: Mapped[str] = mapped_column(String(16))
    session_key: Mapped[str] = mapped_column(String(80))
    step: Mapped[str] = mapped_column(String(20), default="language")
    language: Mapped[str] = mapped_column(String(8), default="en")
    public_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    last_update_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    updated_at: Mapped[datetime]


class Outbound(Base):
    """A message we sent. The audit log stores the label, not this body."""

    __tablename__ = "followup_outbound"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    channel: Mapped[str] = mapped_column(String(16))
    purpose_label: Mapped[str] = mapped_column(String(40))
    mode_label: Mapped[str] = mapped_column(String(20))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime]


class PatientLink(Base):
    """Which card a signed-in patient account or a known handset belongs to.

    A help request from the support chat, USSD or SMS carries no card ID. This link
    lets the task it opens name the case, so the navigator knows who to contact.
    The phone reference stays here, never on a dashboard.
    """

    __tablename__ = "patient_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(20), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, unique=True)
    phone_ref: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True)
    created_at: Mapped[datetime]
