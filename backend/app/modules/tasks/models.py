from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class NavigatorTask(Base):
    """Work for a person. The summary is a fixed sentence, never the patient's own words."""

    __tablename__ = "navigator_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int | None] = mapped_column(
        ForeignKey("care_cases.id"), nullable=True, index=True
    )
    task_type: Mapped[str] = mapped_column(String(40))
    priority: Mapped[str] = mapped_column(String(10), default="normal")
    title: Mapped[str] = mapped_column(String(80))
    summary: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(10), default="open", index=True)  # open | done
    source: Mapped[str] = mapped_column(String(20), default="assistant")
    created_at: Mapped[datetime]
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
