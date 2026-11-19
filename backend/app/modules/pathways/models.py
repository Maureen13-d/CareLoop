from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class CareCase(Base):
    """One tracked screening-to-care journey for one patient."""

    __tablename__ = "care_cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    source_screening_id: Mapped[int | None] = mapped_column(
        ForeignKey("screenings.id"), nullable=True
    )
    pathway_id: Mapped[str] = mapped_column(String(60))
    pathway_version: Mapped[str] = mapped_column(String(20))
    state: Mapped[str] = mapped_column(String(40), index=True)
    urgency: Mapped[str] = mapped_column(String(10), default="routine")  # routine | urgent
    owner_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    owner_department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )
    state_entered_at: Mapped[datetime]
    deadline_at: Mapped[datetime | None] = mapped_column(nullable=True)
    opened_at: Mapped[datetime]
    closed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    closure_reason: Mapped[str | None] = mapped_column(String(60), nullable=True)


class CaseEvent(Base):
    """Append-only timeline of a case."""

    __tablename__ = "case_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("care_cases.id"), index=True)
    from_state: Mapped[str | None] = mapped_column(String(40), nullable=True)
    to_state: Mapped[str] = mapped_column(String(40))
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    actor_type: Mapped[str] = mapped_column(String(10), default="user")  # user | system | ai
    occurred_at: Mapped[datetime]
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("care_cases.id"), index=True)
    type: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text)
    reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    recorded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    recorded_at: Mapped[datetime]


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("care_cases.id"), index=True)
    state: Mapped[str] = mapped_column(String(40))
    level: Mapped[int]
    reason: Mapped[str] = mapped_column(Text)
    raised_at: Mapped[datetime]
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True)
    resolved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
