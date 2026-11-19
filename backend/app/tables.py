"""Database tables. Persistence concerns only: the API and engine use the Pydantic models.
Defense in depth: patient_ref is validated by the Pydantic models AND by a CHECK constraint, so
even a direct SQL insert cannot store a non-synthetic identifier (see docs/DATA_POLICY.md).
"""

from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, Column
from sqlalchemy.types import DateTime, TypeDecorator
from sqlmodel import Field, SQLModel


class UTCDateTime(TypeDecorator):
    """SQLite drops tzinfo. Store UTC; always hand back timezone-aware UTC datetimes."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Naive datetime rejected: use timezone-aware datetimes")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        return None if value is None else value.replace(tzinfo=UTC)


# SQLite equivalent of ^SYN-\d{4,}$ (GLOB has no quantifiers, so: 4+ digits, then digits only).
# NOTE: SQLite-specific syntax. On Postgres use: patient_ref ~ '^SYN-[0-9]{4,}$'
_SYN_SQL = (
    "patient_ref GLOB 'SYN-[0-9][0-9][0-9][0-9]*' AND substr(patient_ref, 5) NOT GLOB '*[^0-9]*'"
)


class CaseRow(SQLModel, table=True):
    __tablename__ = "cases"
    __table_args__ = (CheckConstraint(_SYN_SQL, name="ck_cases_patient_ref_synthetic"),)

    id: str = Field(primary_key=True)
    patient_ref: str = Field(index=True)
    stage: str
    stage_entered_at: datetime = Field(sa_column=Column(UTCDateTime(), nullable=False))


class StageEventRow(SQLModel, table=True):
    """Append-only history of stage changes for a case."""

    __tablename__ = "stage_events"

    id: int | None = Field(default=None, primary_key=True)
    case_id: str = Field(foreign_key="cases.id", index=True)
    stage: str
    occurred_at: datetime = Field(sa_column=Column(UTCDateTime(), nullable=False))


class OutreachEventRow(SQLModel, table=True):
    __tablename__ = "outreach_events"
    __table_args__ = (CheckConstraint(_SYN_SQL, name="ck_outreach_events_patient_ref_synthetic"),)

    id: str = Field(primary_key=True)
    case_id: str = Field(foreign_key="cases.id", index=True)
    patient_ref: str
    stage: str
    kind: str
    channel: str
    attempt: int
    message: str
    status: str
    created_at: datetime = Field(sa_column=Column(UTCDateTime(), nullable=False, index=True))
