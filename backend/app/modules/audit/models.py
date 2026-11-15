from datetime import datetime

from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AuditLog(Base):
    """Append-only record of who did what and when. No update or delete code exists."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    occurred_at: Mapped[datetime]
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    actor_type: Mapped[str] = mapped_column(String(10), default="user")  # user | system | ai
    role: Mapped[str | None] = mapped_column(String(30), nullable=True)
    action: Mapped[str] = mapped_column(String(60), index=True)
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    patient_id: Mapped[int | None] = mapped_column(ForeignKey("patients.id"), nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    outcome: Mapped[str] = mapped_column(String(15), default="success")  # success | denied | rejected
