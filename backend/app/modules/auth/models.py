from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

ROLE_NAVIGATOR = "navigator"  # supports patients; works the worklist (was "coordinator")
ROLE_CLINICIAN = "clinician"  # records screenings; facility-side staff
ROLE_COUNSELLOR = "counsellor"  # takes escalations for distress
ROLE_PATIENT = "patient"  # a patient using the web app (patient login comes later)
ROLE_PROGRAM_MANAGER = "program_manager"
ROLE_ADMIN = "admin"
ROLE_CHW = "chw"  # community health promoter; own women only, not clinical state changes
ROLE_KSL_REVIEWER = "ksl_reviewer"  # Deaf reviewer; can pass or fail a clip, cannot approve alone
ROLES = (
    ROLE_NAVIGATOR,
    ROLE_CLINICIAN,
    ROLE_COUNSELLOR,
    ROLE_PATIENT,
    ROLE_PROGRAM_MANAGER,
    ROLE_ADMIN,
    ROLE_CHW,
    ROLE_KSL_REVIEWER,
)


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True)  # machine name used in pathway files
    label: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(40), default="clinical")


class User(Base):
    """Demo staff account. Roles are permissions, not fixed job titles."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(60), unique=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(30))
    display_name: Mapped[str] = mapped_column(String(100))
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    active: Mapped[bool] = mapped_column(default=True)
