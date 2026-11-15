"""Create the demo database with SYNTHETIC data.

Run from anywhere:
    python database/seeds/seed_demo.py --reset

Everything generated here is fake: "Demo Patient 001", demo zones, demo accounts.
The numbers below are ASSUMPTIONS chosen to make a realistic-looking demo, not
measurements. They are not evidence about any real health system.

  - Each step takes a random time centred a little under its deadline (log-normal),
    so roughly a third of steps run late.
  - About 7% of cases silently stall at a step (the patient is never moved on).
  - About 15% of confirmed cases need no treatment and close as confirmed_negative.
  - About 12% of screened-positive cases are flagged suspected cancer (urgent).
"""
import argparse
import random
import sys
from datetime import timedelta
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select  # noqa: E402

from app.core import clock  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.db import Base, SessionLocal, engine, import_models, init_db  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.modules.auth.models import Department, User  # noqa: E402
from app.modules.patients.models import Consent, Patient  # noqa: E402
from app.modules.pathways import service as pathways  # noqa: E402
from app.modules.pathways.loader import load_pathway  # noqa: E402
from app.modules.pathways.models import CareCase  # noqa: E402
from app.modules.screenings.models import Screening  # noqa: E402

DEPARTMENTS = [
    ("screening_clinic", "Screening clinic", "clinical"),
    ("care_coordination", "Care coordination", "administrative"),
    ("gynaecology_clinic", "Gynaecology clinic", "clinical"),
    ("treatment_unit", "Treatment unit", "clinical"),
]
USERS = [  # username, role, display name, department
    ("coordinator", "coordinator", "Demo Coordinator", "care_coordination"),
    ("clinician", "clinician", "Demo Clinician", "gynaecology_clinic"),
    ("manager", "program_manager", "Demo Program Manager", None),
    ("admin", "admin", "Demo Admin", None),
]
FLOW = ["PATIENT_NOTIFIED", "PATIENT_ACKNOWLEDGED", "CONFIRMATION_SCHEDULED", "CONFIRMATION_COMPLETED",
        "REFERRAL_SENT", "REFERRAL_ACCEPTED", "TREATMENT_STARTED", "FOLLOW_UP_DUE"]
P_STALL = 0.07
P_NO_TREATMENT_NEEDED = 0.15
P_URGENT = 0.12


def step_hours(rng: random.Random, deadline_hours: int) -> float:
    return deadline_hours * rng.lognormvariate(-0.3, 0.7)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed synthetic CareLoop demo data")
    parser.add_argument("--reset", action="store_true", help="delete all existing data first")
    parser.add_argument("--cases", type=int, default=40, help="screened-positive synthetic patients")
    parser.add_argument("--negatives", type=int, default=10, help="screened-negative synthetic patients")
    parser.add_argument("--seed", type=int, default=42, help="random seed, for repeatable demos")
    args = parser.parse_args()

    import_models()
    if args.reset:
        Base.metadata.drop_all(engine)
    init_db()
    db = SessionLocal()
    if db.scalar(select(User.id)) is not None:
        sys.exit("Database already has data. Run again with --reset to rebuild it.")

    rng = random.Random(args.seed)
    clock.reset()
    now = clock.now()
    pw = load_pathway()

    depts = {}
    for name, label, kind in DEPARTMENTS:
        depts[name] = Department(name=name, label=label, type=kind)
        db.add(depts[name])
    db.flush()
    users = {}
    for username, role, display, dept in USERS:
        users[username] = User(username=username, password_hash=hash_password(settings.demo_password), role=role,
                               display_name=display, department_id=depts[dept].id if dept else None)
        db.add(users[username])
    db.commit()

    age_bands = ["25-29", "30-34", "35-39", "40-44", "45-49"]
    zones = ["Demo Zone A", "Demo Zone B", "Demo Zone C"]

    def new_patient(number: int) -> Patient:
        patient = Patient(patient_ref=f"CL-{number:06d}", display_name=f"Demo Patient {number:03d}",
                          age_band=rng.choice(age_bands), zone=rng.choice(zones),
                          preferred_language="sw" if rng.random() < 0.3 else "en")
        db.add(patient)
        db.flush()
        return patient

    number = 0
    for _ in range(args.negatives):
        number += 1
        patient = new_patient(number)
        when = now - timedelta(days=rng.uniform(1, 50))
        db.add(Screening(patient_id=patient.id, screening_type=rng.choice(["HPV_DNA", "VIA"]), result="negative",
                         performed_at=when, department_id=depts["screening_clinic"].id, recorded_by=users["clinician"].id))
    db.commit()

    for _ in range(args.cases):
        number += 1
        patient = new_patient(number)
        start = now - timedelta(days=rng.uniform(1, 50))
        db.add(Consent(patient_id=patient.id, purpose="care_coordination", granted=True, granted_at=start))
        screening = Screening(patient_id=patient.id, screening_type=rng.choice(["HPV_DNA", "VIA"]),
                              result="suspected_cancer" if rng.random() < P_URGENT else "positive",
                              performed_at=start, department_id=depts["screening_clinic"].id, recorded_by=users["clinician"].id)
        db.add(screening)
        db.flush()
        case = pathways.open_case(db, patient, screening, users["clinician"], at=start)
        db.commit()

        ts = start
        for state in FLOW:
            previous = pw.states[case.state]
            ts = ts + timedelta(hours=step_hours(rng, previous.deadline_hours))
            if ts > now or rng.random() < P_STALL:
                break
            pathways.transition(db, case, state, None, at=ts)
            if state == "CONFIRMATION_COMPLETED" and rng.random() < P_NO_TREATMENT_NEEDED:
                ts = ts + timedelta(hours=rng.uniform(2, 48))
                if ts <= now:
                    pathways.close_case(db, case, None, "confirmed_negative", "Synthetic: no treatment needed", at=ts)
                break
        else:
            ts = ts + timedelta(hours=step_hours(rng, pw.states["FOLLOW_UP_DUE"].deadline_hours))
            if ts <= now and rng.random() > P_STALL:
                pathways.close_case(db, case, None, "follow_up_completed", "Synthetic: follow-up completed", at=ts)

    # Some open cases already have an owner; others stay unowned so the worklist shows both.
    for case in db.scalars(select(CareCase).where(CareCase.state.not_in(list(pw.terminal_states)))).all():
        if rng.random() < 0.4:
            pathways.claim_case(db, case, users["coordinator"])

    created = pathways.run_deadline_check(db, now)

    states = {}
    for case in db.scalars(select(CareCase)).all():
        states[case.state] = states.get(case.state, 0) + 1
    overdue = len(db.scalars(select(CareCase.id).where(CareCase.deadline_at.is_not(None), CareCase.deadline_at < now)).all())
    print(f"Seeded {args.cases + args.negatives} synthetic patients and {sum(states.values())} cases.")
    for state, count in sorted(states.items(), key=lambda kv: -kv[1]):
        print(f"  {state:<24} {count}")
    print(f"Overdue now: {overdue}. Escalations raised: {len(created)}.")
    print("\nDemo accounts (synthetic, password from DEMO_PASSWORD):")
    for username, role, _, _ in USERS:
        print(f"  {username:<12} role={role}")
    print(f"  password: {settings.demo_password}")
    db.close()


if __name__ == "__main__":
    main()
