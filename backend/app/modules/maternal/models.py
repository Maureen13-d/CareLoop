"""Maternal pathway records. Synthetic only.

Devices store a pseudonymous id, never a name. Readings, check-ins and band events
store labels, never free text a woman typed.
"""

from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Pregnancy(Base):
    __tablename__ = "pregnancies"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    gestation_band: Mapped[str] = mapped_column(String(20))
    area_label: Mapped[str] = mapped_column(String(40))
    consent_care_coordination: Mapped[bool] = mapped_column(default=False)
    consent_sms_reminders: Mapped[bool] = mapped_column(default=False)
    consent_band_contact: Mapped[bool] = mapped_column(default=False)
    assigned_chw_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime]


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(10))  # hub | band
    pseudonymous_device_id: Mapped[str] = mapped_column(String(40), unique=True)
    api_key_hash: Mapped[str] = mapped_column(String(200))
    assigned_chw_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    assigned_pregnancy_id: Mapped[int | None] = mapped_column(
        ForeignKey("pregnancies.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="active")
    last_seen_at: Mapped[datetime | None] = mapped_column(nullable=True)
    battery_pct: Mapped[int | None] = mapped_column(nullable=True)


class Reading(Base):
    __tablename__ = "readings"
    __table_args__ = (
        UniqueConstraint("device_id", "client_reading_id", name="uq_reading_device_client"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    pregnancy_id: Mapped[int] = mapped_column(ForeignKey("pregnancies.id"), index=True)
    device_id: Mapped[int | None] = mapped_column(ForeignKey("devices.id"), nullable=True)
    client_reading_id: Mapped[str] = mapped_column(String(80))
    systolic: Mapped[int | None] = mapped_column(nullable=True)
    diastolic: Mapped[int | None] = mapped_column(nullable=True)
    pulse: Mapped[int | None] = mapped_column(nullable=True)
    urine_protein: Mapped[str | None] = mapped_column(String(10), nullable=True)
    hb_band: Mapped[str | None] = mapped_column(String(10), nullable=True)
    danger_signs: Mapped[list] = mapped_column(JSON)
    risk_level: Mapped[str] = mapped_column(String(10))
    hub_local_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    level_mismatch: Mapped[bool] = mapped_column(default=False)
    rule_ids: Mapped[list] = mapped_column(JSON)
    rules_version: Mapped[str] = mapped_column(String(40))
    source: Mapped[str] = mapped_column(String(10))
    taken_at: Mapped[datetime]
    received_at: Mapped[datetime]


class BandEvent(Base):
    __tablename__ = "band_events"
    __table_args__ = (UniqueConstraint("device_id", "event_id", name="uq_band_device_event"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    pregnancy_id: Mapped[int] = mapped_column(ForeignKey("pregnancies.id"), index=True)
    event_id: Mapped[str] = mapped_column(String(80))
    type: Mapped[str] = mapped_column(String(20))
    hr: Mapped[int | None] = mapped_column(nullable=True)
    spo2: Mapped[int | None] = mapped_column(nullable=True)
    ts: Mapped[datetime]
    received_at: Mapped[datetime]


class BandCommand(Base):
    __tablename__ = "band_commands"

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime]
    acked_at: Mapped[datetime | None] = mapped_column(nullable=True)


class CheckIn(Base):
    __tablename__ = "checkins"

    id: Mapped[int] = mapped_column(primary_key=True)
    pregnancy_id: Mapped[int] = mapped_column(ForeignKey("pregnancies.id"), index=True)
    channel: Mapped[str] = mapped_column(String(10))
    answers: Mapped[dict] = mapped_column(JSON)
    risk_level: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime]


class Voucher(Base):
    """Simulated transport help. Not a real payment."""

    __tablename__ = "vouchers"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("care_cases.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    amount_label: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20))
    simulated_provider: Mapped[str] = mapped_column(String(40), default="SIMULATED_MPESA")
    created_at: Mapped[datetime]


class Barrier(Base):
    """A confirmed practical barrier. The flag is a label, never a sentence."""

    __tablename__ = "barriers"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("care_cases.id"), index=True)
    flag: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime]


class CoverCheck(Base):
    """Simulated cover lookup. Not a live SHA or TaifaCare call."""

    __tablename__ = "cover_checks"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("care_cases.id"), index=True)
    status: Mapped[str] = mapped_column(String(20))
    source: Mapped[str] = mapped_column(String(40), default="SIMULATED_SHA")
    created_at: Mapped[datetime]
