"""Find the case behind a help request that arrives without a card ID.

The support chat knows the signed-in account. USSD and SMS know only the handset.
Both are matched to a card here so the task they open names the person. When no
match exists the task still opens, unlinked, exactly as before.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.modules.auth.models import User
from app.modules.followup.models import ContactVault, Enrolment, PatientLink

# The demo patient account and the handset on the Basic phone page share one card.
# The frontend pre-fills the same ID (frontend/src/lib/demoCard.ts).
DEMO_PATIENT_USERNAME = "aisha"
DEMO_CARD_ID = "M7P7-R26M-PYSX-W"
DEMO_HANDSET = "+254700000101"


def _digits(value: str | None) -> str:
    """Compare phone numbers by digits, treating 07... and +2547... as the same line."""
    digits = "".join(char for char in (value or "") if char.isdigit())
    if digits.startswith("0") and len(digits) == 10:
        digits = "254" + digits[1:]
    return digits


def _case_for_public_id(db: Session, public_id: str | None) -> int | None:
    if not public_id:
        return None
    return db.scalar(select(Enrolment.case_id).where(Enrolment.public_id == public_id))


def case_for_user(db: Session, user) -> int | None:
    if user is None:
        return None
    link = db.scalar(select(PatientLink).where(PatientLink.user_id == user.id))
    return _case_for_public_id(db, link.public_id if link else None)


def case_for_phone(db: Session, phone_ref: str | None) -> int | None:
    wanted = _digits(phone_ref)
    if len(wanted) < 6:
        return None
    for link in db.scalars(select(PatientLink).where(PatientLink.phone_ref.is_not(None))):
        if _digits(link.phone_ref) == wanted:
            return _case_for_public_id(db, link.public_id)
    for vault in db.scalars(select(ContactVault)):
        if _digits(vault.contact_ref) == wanted:
            found = _case_for_public_id(db, vault.public_id)
            if found is not None:
                return found
    return None


def ensure_demo_patient(db: Session) -> None:
    """Give the demo patient account its own card and booklet, once. Safe to run on every start."""
    patient_user = db.scalar(select(User).where(User.username == DEMO_PATIENT_USERNAME))
    if patient_user is None:
        return
    link = db.scalar(select(PatientLink).where(PatientLink.user_id == patient_user.id))
    if link is None:
        enrolment = db.scalar(select(Enrolment).where(Enrolment.public_id == DEMO_CARD_ID))
        if enrolment is None:
            enrolment = _issue_demo_card(db, patient_user)
            if enrolment is None:
                return
        handset_taken = db.scalar(
            select(PatientLink.id).where(PatientLink.phone_ref == DEMO_HANDSET)
        )
        link = PatientLink(
            public_id=enrolment.public_id,
            user_id=patient_user.id,
            phone_ref=None if handset_taken else DEMO_HANDSET,
            created_at=clock.now(),
        )
        db.add(link)
        db.commit()
    _ensure_demo_pregnancy(db, link)


def _patient_for_link(db: Session, link: PatientLink | None):
    from app.modules.patients.models import Patient

    if link is None:
        return None
    enrolment = db.scalar(select(Enrolment).where(Enrolment.public_id == link.public_id))
    return db.get(Patient, enrolment.patient_id) if enrolment else None


def _ensure_demo_pregnancy(db: Session, link: PatientLink) -> None:
    """A synthetic booklet, so the Cuff hub on the patient account has somewhere to send."""
    from app.modules.maternal.models import Pregnancy

    patient = _patient_for_link(db, link)
    if patient is None:
        return
    if db.scalar(select(Pregnancy.id).where(Pregnancy.patient_id == patient.id)):
        return
    chw = db.scalar(select(User).where(User.username == "grace", User.role == "chw"))
    db.add(
        Pregnancy(
            patient_id=patient.id,
            gestation_band="28-36w",
            area_label=patient.zone,
            consent_care_coordination=True,
            consent_sms_reminders=True,
            consent_band_contact=False,
            assigned_chw_id=chw.id if chw else None,
            created_at=clock.now(),
        )
    )
    db.commit()


def booklet_for_user(db: Session, user) -> str | None:
    """The booklet reference a signed-in patient's hub sends readings to, if any."""
    from app.modules.maternal.models import Pregnancy

    if user is None:
        return None
    link = db.scalar(select(PatientLink).where(PatientLink.user_id == user.id))
    patient = _patient_for_link(db, link)
    if patient is None:
        return None
    if not db.scalar(select(Pregnancy.id).where(Pregnancy.patient_id == patient.id)):
        return None
    return patient.patient_ref


def _issue_demo_card(db: Session, patient_user: User) -> Enrolment | None:
    from app.modules.followup.register import register_followup
    from app.modules.followup.schemas import RegisterIn
    from app.modules.patients.models import Patient

    clinician = db.scalar(select(User).where(User.username == "david"))
    has_chw = db.scalar(select(User.id).where(User.username == "grace", User.role == "chw"))
    opened = register_followup(
        db,
        clinician,
        RegisterIn(
            age_band="30-34",
            area_label="Zone A",
            screening_type="cervical",
            finding="concerning",
            consent=True,
            language="en",
            channel="web",
            contact=DEMO_HANDSET,
            assigned_chw_username="grace" if has_chw else None,
        ),
        public_id=DEMO_CARD_ID,
    )
    enrolment = db.scalar(select(Enrolment).where(Enrolment.public_id == opened.get("public_id")))
    if enrolment is None:
        return None
    patient = db.get(Patient, enrolment.patient_id)
    if patient is not None:
        # The account has a (fictional) name, so the navigator sees who asked.
        patient.display_name = patient_user.display_name
    db.flush()
    return enrolment
