from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class HospitalLink(Base):
    """The simulated clinic's appointment id for one case. Not a real hospital record."""

    __tablename__ = "hospital_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("care_cases.id"), unique=True, index=True)
    appointment_id: Mapped[str] = mapped_column(String(40))
    location_ref: Mapped[str] = mapped_column(String(40))
    milestones: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime]
