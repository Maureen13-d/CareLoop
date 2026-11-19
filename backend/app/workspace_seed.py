"""Synthetic staff, patients and cases so the desk is not empty on a first run.

All names are fictional. Nothing here is a real person or a real clinic.
"""

import os
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.config import settings
from app.core.security import hash_password
from app.modules.auth.models import Department, User
from app.modules.channels.service import seed_reminder
from app.modules.pathways.models import CareCase
from app.modules.pathways.service import claim_case, run_deadline_check, transition
from app.modules.patients.schemas import ConsentIn, PatientCreate
from app.modules.patients.service import create_patient, record_consent
from app.modules.screenings.schemas import ScreeningIn
from app.modules.screenings.service import record_screening
from app.modules.tasks.service import create_task

DEPARTMENTS = (
    ("screening_clinic", "Screening clinic", "clinical"),
    ("navigation_team", "Navigation team", "navigation"),
    ("facility", "Facility", "clinical"),
    ("hospital", "Hospital", "clinical"),
)

USERS = (
    ("amina", "navigator", "navigation_team", "Amina Otieno"),
    ("david", "clinician", "screening_clinic", "David Kamau"),
    ("wanjiku", "counsellor", None, "Wanjiku Njeri"),
    ("peter", "program_manager", None, "Peter Omondi"),
    ("admin", "admin", None, "Demo Admin"),
    ("aisha", "patient", None, "Aisha Demo"),
)

TO_HANDOFF = (
    "PATIENT_ENGAGED",
    "BARRIERS_ASSESSED",
    "NAVIGATION_ACTIVE",
    "APPOINTMENT_BOOKED",
    "ARRIVAL_CONFIRMED",
    "HANDED_OFF",
)

STORIES = (
    {
        "name": "Demo Achieng",
        "age": "30-34",
        "zone": "Demo Zone Kisumu",
        "result": "positive",
        "kind": "HPV_DNA",
        "states": (),
    },
    {
        "name": "Demo Njeri",
        "age": "35-39",
        "zone": "Demo Zone Nairobi",
        "result": "positive",
        "kind": "VIA",
        "states": ("PATIENT_ENGAGED",),
    },
    {
        "name": "Demo Wairimu",
        "age": "40-44",
        "zone": "Demo Zone Kisumu",
        "result": "positive",
        "kind": "HPV_DNA",
        "states": ("PATIENT_ENGAGED", "BARRIERS_ASSESSED"),
        "overdue_hours": 8,
    },
    {
        "name": "Demo Atieno",
        "age": "25-29",
        "zone": "Demo Zone Mombasa",
        "result": "positive",
        "kind": "CYTOLOGY",
        "states": ("PATIENT_ENGAGED", "BARRIERS_ASSESSED", "NAVIGATION_ACTIVE"),
        "claim": True,
    },
    {
        "name": "Demo Chebet",
        "age": "45-49",
        "zone": "Demo Zone Eldoret",
        "result": "positive",
        "kind": "VIA",
        "states": (
            "PATIENT_ENGAGED",
            "BARRIERS_ASSESSED",
            "NAVIGATION_ACTIVE",
            "APPOINTMENT_BOOKED",
        ),
    },
    {
        "name": "Demo Akinyi",
        "age": "30-34",
        "zone": "Demo Zone Kisumu",
        "result": "positive",
        "kind": "HPV_DNA",
        "states": TO_HANDOFF[:5],
    },
    {
        "name": "Demo Moraa",
        "age": "35-39",
        "zone": "Demo Zone Nairobi",
        "result": "suspected_cancer",
        "kind": "VIA",
        "states": ("PATIENT_ENGAGED",),
    },
    {
        "name": "Demo Nyambura",
        "age": "40-44",
        "zone": "Demo Zone Nakuru",
        "result": "positive",
        "kind": "HPV_DNA",
        "states": TO_HANDOFF,
    },
)


def workspace_seed_enabled() -> bool:
    return os.environ.get("CARELOOP_SEED_WORKSPACE", "true").lower() not in {"0", "false", "no"}


def seed_workspace_if_empty(db: Session, *, force: bool = False) -> None:
    """Create demo accounts and a spread of cases when the desk is empty."""
    if not force and not workspace_seed_enabled():
        return
    has_amina = db.scalar(select(User.id).where(User.username == "amina"))
    has_anyone = db.scalar(select(User.id))
    if has_amina is None and has_anyone is None:
        _create_users(db)
    elif has_amina is None:
        return
    if db.scalar(select(CareCase.id)) is not None:
        return
    _create_cases(db)


def _create_users(db: Session) -> None:
    departments = {}
    for name, label, kind in DEPARTMENTS:
        department = Department(name=name, label=label, type=kind)
        db.add(department)
        departments[name] = department
    db.flush()
    password_hash = hash_password(settings.demo_password)
    for username, role, department, display_name in USERS:
        db.add(
            User(
                username=username,
                password_hash=password_hash,
                role=role,
                display_name=display_name,
                department_id=departments[department].id if department else None,
            )
        )
    db.commit()


def _create_cases(db: Session) -> None:
    clinician = db.scalar(select(User).where(User.username == "david"))
    navigator = db.scalar(select(User).where(User.username == "amina"))
    overdue = None
    navigating = None
    for story in STORIES:
        patient = create_patient(
            db,
            clinician,
            PatientCreate(
                display_name=story["name"],
                age_band=story["age"],
                zone=story["zone"],
            ),
        )
        record_consent(db, clinician, patient, ConsentIn(purpose="care_coordination", granted=True))
        record_consent(db, clinician, patient, ConsentIn(purpose="sms_reminders", granted=True))
        _screening, case, status, message = record_screening(
            db,
            clinician,
            patient,
            ScreeningIn(screening_type=story["kind"], result=story["result"]),
        )
        if status != "opened" or case is None:
            raise RuntimeError(message)
        for state in story["states"]:
            case = transition(db, case, state, clinician, "Synthetic demo step")
        if story.get("overdue_hours"):
            case.deadline_at = clock.now() - timedelta(hours=story["overdue_hours"])
            db.commit()
            overdue = case
        if story.get("claim"):
            case = claim_case(db, case, navigator)
            navigating = case
    run_deadline_check(db)
    if overdue is not None:
        create_task(
            db,
            task_type="counsellor_contact",
            priority="high",
            case_id=overdue.id,
            source="system",
        )
    if navigating is not None:
        create_task(
            db,
            task_type="navigator_followup",
            priority="normal",
            case_id=navigating.id,
            source="system",
        )
    db.commit()
    seed_reminder(db)
