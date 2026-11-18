from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Screening(Base):
    __tablename__ = "screenings"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    screening_type: Mapped[str] = mapped_column(String(20))
    result: Mapped[str] = mapped_column(String(20))
    performed_at: Mapped[datetime]
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    recorded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
