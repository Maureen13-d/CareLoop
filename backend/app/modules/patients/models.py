from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

CONSENT_PURPOSE_COORDINATION = "care_coordination"
CONSENT_PURPOSES = (
    CONSENT_PURPOSE_COORDINATION,
    "sms_reminders",
    "data_sharing_between_facilities",
)


class Patient(Base):
    """Synthetic patient. Identified only by a pseudonymous reference."""

    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_ref: Mapped[str] = mapped_column(String(20), unique=True)
    display_name: Mapped[str] = mapped_column(
        String(100)
    )  # synthetic, for example "Demo Patient 007"
    age_band: Mapped[str] = mapped_column(String(10))
    zone: Mapped[str] = mapped_column(String(40))  # synthetic area label
    preferred_language: Mapped[str] = mapped_column(String(20), default="en")
    is_synthetic: Mapped[bool] = mapped_column(default=True)


class Consent(Base):
    __tablename__ = "consents"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    purpose: Mapped[str] = mapped_column(String(50))
    granted: Mapped[bool]
    granted_at: Mapped[datetime]
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True)
