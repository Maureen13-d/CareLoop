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
from app.modules.maternal.models import CoverCheck, Device, Pregnancy, Reading, Voucher
from app.modules.maternal.service import open_maternal_case
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
    ("community", "Community", "community"),
)

USERS = (
    ("amina", "navigator", "navigation_team", "Amina Otieno"),
    ("david", "clinician", "screening_clinic", "David Kamau"),
    ("wanjiku", "counsellor", None, "Wanjiku Njeri"),
    ("peter", "program_manager", None, "Peter Omondi"),
    ("admin", "admin", None, "Demo Admin"),
    ("aisha", "patient", None, "Aisha Demo"),
    ("grace", "chw", "community", "Grace Achieng"),
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
    _create_maternal(db)
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
    _create_followup(db)


# Synthetic women on the maternal pathway. Names are fictional.
# state walk uses the role allowed to enter each state. Red journeys are urgent.
_MATERNAL_ACTOR = {
    "home_screened": "grace",
    "risk_flagged": None,
    "navigating": "amina",
    "visit_booked": "amina",
    "delivery_planned": "amina",
    "arrived": "david",
    "with_hospital": "david",
    "postnatal_watch": "amina",
}

MATERNAL_WOMEN = (
    {
        "name": "Mercy Demo",
        "age": "20-24",
        "zone": "Demo Zone Kisumu",
        "band": "28-36w",
        "states": (),
        "sms": True,
        "band_contact": True,
    },
    {
        "name": "Demo Awuor",
        "age": "25-29",
        "zone": "Demo Zone Kisumu",
        "band": "20-28w",
        "states": ("home_screened",),
        "sms": True,
        "band_contact": False,
    },
    {
        "name": "Demo Adhiambo",
        "age": "30-34",
        "zone": "Demo Zone Siaya",
        "band": "28-36w",
        "states": ("home_screened", "risk_flagged"),
        "urgent": True,
        "sms": True,
        "band_contact": True,
        "reading": True,
    },
    {
        "name": "Demo Nafula",
        "age": "20-24",
        "zone": "Demo Zone Kakamega",
        "band": "36w+",
        "states": ("home_screened", "navigating"),
        "sms": True,
        "band_contact": False,
        "voucher": True,
    },
    {
        "name": "Demo Kerubo",
        "age": "25-29",
        "zone": "Demo Zone Kisumu",
        "band": "<20w",
        "states": ("home_screened", "navigating", "visit_booked"),
        "sms": False,
        "band_contact": False,
    },
    {
        "name": "Demo Chemutai",
        "age": "30-34",
        "zone": "Demo Zone Eldoret",
        "band": "36w+",
        "states": (
            "home_screened",
            "navigating",
            "visit_booked",
            "arrived",
            "with_hospital",
            "postnatal_watch",
        ),
        "sms": True,
        "band_contact": False,
    },
)


def _create_maternal(db: Session) -> None:
    grace = db.scalar(select(User).where(User.username == "grace"))
    amina = db.scalar(select(User).where(User.username == "amina"))
    david = db.scalar(select(User).where(User.username == "david"))
    actors = {"grace": grace, "amina": amina, "david": david, None: None}
    device_hash = hash_password("synthetic-device-key")
    hub = Device(
        kind="hub",
        pseudonymous_device_id="HUB-0007",
        api_key_hash=device_hash,
        assigned_chw_id=grace.id,
        status="active",
        last_seen_at=clock.now(),
    )
    db.add(hub)
    db.flush()
    flagged_pregnancy = None
    flagged_case = None
    for story in MATERNAL_WOMEN:
        patient = create_patient(
            db,
            david,
            PatientCreate(display_name=story["name"], age_band=story["age"], zone=story["zone"]),
        )
        record_consent(db, david, patient, ConsentIn(purpose="care_coordination", granted=True))
        if story["sms"]:
            record_consent(db, david, patient, ConsentIn(purpose="sms_reminders", granted=True))
        pregnancy = Pregnancy(
            patient_id=patient.id,
            gestation_band=story["band"],
            area_label=story["zone"],
            consent_care_coordination=True,
            consent_sms_reminders=story["sms"],
            consent_band_contact=story["band_contact"],
            assigned_chw_id=grace.id,
            created_at=clock.now(),
        )
        db.add(pregnancy)
        db.commit()
        case = open_maternal_case(db, patient, pregnancy, grace)
        for state in story["states"]:
            if state == "risk_flagged" and story.get("urgent"):
                case.urgency = "urgent"
                db.commit()
            case = transition(db, case, state, actors[_MATERNAL_ACTOR[state]], "Synthetic demo step")
        if story.get("reading"):
            flagged_pregnancy = pregnancy
            flagged_case = case
        if story.get("voucher"):
            now = clock.now()
            db.add(
                Voucher(
                    case_id=case.id,
                    kind="transport",
                    amount_label="assumed",
                    status="requested",
                    simulated_provider="SIMULATED_MPESA",
                    created_at=now,
                )
            )
            db.add(
                CoverCheck(
                    case_id=case.id,
                    status="unknown",
                    source="SIMULATED_SHA",
                    created_at=now,
                )
            )
            db.commit()
    if flagged_pregnancy is not None and flagged_case is not None:
        now = clock.now()
        db.add(
            Reading(
                pregnancy_id=flagged_pregnancy.id,
                device_id=hub.id,
                client_reading_id="HUB-0007-000231",
                systolic=152,
                diastolic=98,
                pulse=88,
                urine_protein="2+",
                hb_band="unknown",
                danger_signs=["headache_severe", "vision_blurred"],
                risk_level="red",
                rule_ids=["SEED_LABEL"],
                rules_version="0.1-pending-clinical-review",
                source="hub",
                taken_at=now,
                received_at=now,
            )
        )
        band = Device(
            kind="band",
            pseudonymous_device_id="BAND-0012",
            api_key_hash=device_hash,
            assigned_chw_id=grace.id,
            assigned_pregnancy_id=flagged_pregnancy.id,
            status="lent",
            last_seen_at=now,
            battery_pct=63,
        )
        db.add(band)
        db.commit()


def _create_followup(db: Session) -> None:
    """Ten to twelve synthetic follow-up journeys for the CHW worklist. IDs, not names."""
    from app.modules.followup.models import Enrolment
    from app.modules.followup.register import register_followup
    from app.modules.followup.schemas import RegisterIn

    david = db.scalar(select(User).where(User.username == "david"))
    stories = (
        ("concerning", "screened", 9, "none", 0, None),
        ("concerning", "screened", 1, "worse", 0, None),
        ("concerning", "contacted", 4, "none", 0, None),
        ("concerning", "joined", 3, "none", 0, None),
        ("concerning", "barrier_identified", 6, "none", 0, "transport"),
        ("urgent", "navigating", 2, "none", 0, None),
        ("concerning", "visit_booked", 5, "none", 0, None),
        ("concerning", "screened", 8, "none", 3, None),
        ("concerning", "arrived", 7, "none", 0, None),
        ("concerning", "with_hospital", 10, "none", 0, None),
        ("concerning", "screened", 2, "none", 0, "fear"),
        ("concerning", "joined", 3, "none", 0, "where"),
    )
    walks = {
        "contacted": ["contacted"],
        "joined": ["contacted", "joined"],
        "barrier_identified": ["contacted", "joined", "barrier_identified"],
        "navigating": ["contacted", "joined", "navigating"],
        "visit_booked": ["contacted", "joined", "navigating", "visit_booked"],
        "arrived": ["arrived"],
        "with_hospital": ["arrived", "with_hospital"],
    }
    for index, (finding, state, days, symptom, missed, barrier) in enumerate(stories):
        opened = register_followup(
            db,
            david,
            RegisterIn(
                age_band="30-34",
                area_label=("Zone A", "Zone B", "Zone C", "Zone D")[index % 4],
                screening_type="general",
                finding=finding,
                consent=True,
                language="sw" if index % 2 else "en",
                channel=("telegram", "sms", "ussd", "web")[index % 4],
                contact=f"071000{index:04d}",
                assigned_chw_username="grace",
            ),
        )
        case = db.get(CareCase, opened["case_id"])
        for step in walks.get(state, []):
            case = transition(db, case, step, None, "synthetic_step")
        enrolment = db.scalar(select(Enrolment).where(Enrolment.public_id == opened["public_id"]))
        enrolment.symptom_flag = symptom
        enrolment.missed_replies = missed
        enrolment.barrier_label = barrier
        enrolment.opened_at = clock.now() - timedelta(days=days)
        case.opened_at = enrolment.opened_at
        if state not in {"arrived", "with_hospital"} and days >= 5:
            case.deadline_at = clock.now() - timedelta(hours=2)
        db.commit()
    run_deadline_check(db)
