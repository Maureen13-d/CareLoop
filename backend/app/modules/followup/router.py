"""HTTP surface for follow-up. Cervical and maternal routes are unchanged."""

from fastapi import APIRouter, Depends, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_roles
from app.core.errors import DomainError
from app.modules.auth.models import (
    ROLE_ADMIN,
    ROLE_CHW,
    ROLE_CLINICIAN,
    ROLE_NAVIGATOR,
    ROLE_PROGRAM_MANAGER,
)
from app.modules.followup import access, checkins, facility, register, telegram, worklist
from app.modules.followup.access import REJECTED, read_token
from app.modules.followup.cohort import build_cohort, report
from app.modules.followup.conversation import (
    get_session,
    guide_speaks,
    handle,
    respond,
    ussd_contract,
)
from app.modules.followup.ids import parse_public_id
from app.modules.followup.models import Enrolment
from app.modules.followup.schemas import (
    CheckIn,
    OutcomeIn,
    RegisterIn,
    TalkIn,
    TelegramIn,
)
from app.modules.followup.texts import slip_lines

router = APIRouter(prefix="/followup", tags=["followup"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
screener = require_roles(ROLE_CLINICIAN)
staff = require_roles(ROLE_CLINICIAN, ROLE_NAVIGATOR, ROLE_ADMIN, ROLE_PROGRAM_MANAGER, ROLE_CHW)
facility_reader = require_roles(ROLE_CLINICIAN, ROLE_NAVIGATOR, ROLE_ADMIN, ROLE_PROGRAM_MANAGER)
dev_reader = require_roles(ROLE_ADMIN, ROLE_CLINICIAN)


def _patient_id(token: str | None = Depends(oauth2_scheme)) -> str:
    public_id = read_token(token)
    if not public_id:
        raise DomainError(401, "not_authenticated", REJECTED)
    return public_id


def _qr(value: str) -> str | None:
    try:
        import segno
    except ImportError:
        return None
    return segno.make(value, error="m").svg_inline(scale=4)


@router.post("/register", status_code=201)
def post_register(data: RegisterIn, db: Session = Depends(get_db), user=Depends(screener)):
    result = register.register_followup(db, user, data)
    result["synthetic"] = True
    result["review"] = "PENDING CLINICAL REVIEW"
    return result


@router.get("/slip/{public_id}")
def get_slip(public_id: str, db: Session = Depends(get_db), _user=Depends(screener)):
    enrolment = db.scalar(select(Enrolment).where(Enrolment.public_id == public_id))
    if enrolment is None:
        raise DomainError(404, "not_found", "ID not found")
    qr_value = enrolment.public_id
    deep_link = None
    if enrolment.channel == "telegram":
        deep_link = telegram.slip_link(db, enrolment.public_id)
        db.commit()
        qr_value = deep_link
    return {
        "synthetic": True,
        "public_id": enrolment.public_id,
        "lines": slip_lines(enrolment.language),
        "qr_svg": _qr(qr_value),
        "deep_link": deep_link,
    }


@router.post("/access/start")
def start_access(data: CheckIn, db: Session = Depends(get_db)):
    canonical = parse_public_id(data.public_id)
    found = None
    if canonical:
        found = db.scalar(select(Enrolment).where(Enrolment.public_id == canonical))
    if found is not None:
        access.issue_code(db, found.public_id)
        db.commit()
    return {"status": "sent", "synthetic": True}


@router.post("/access/check")
def check_access(data: CheckIn, db: Session = Depends(get_db)):
    canonical = parse_public_id(data.public_id)
    ok = False
    if canonical:
        ok = access.code_ok(db, canonical, data.code, data.client_key)
        db.commit()
    if not ok:
        raise DomainError(401, "not_authenticated", REJECTED)
    return {"access_token": access.issue_token(canonical), "synthetic": True}


@router.get("/access/dev-code")
def dev_code(public_id: str, _user=Depends(dev_reader)):
    if not access.expose_codes():
        raise DomainError(404, "not_found", "Not available")
    code = access.dev_code(public_id)
    if not code:
        raise DomainError(404, "not_found", "No simulated code")
    return {"public_id": public_id, "simulated_code": code, "simulated": True, "synthetic": True}


@router.get("/me")
def me(public_id: str = Depends(_patient_id), db: Session = Depends(get_db)):
    enrolment = db.scalar(select(Enrolment).where(Enrolment.public_id == public_id))
    if enrolment is None:
        raise DomainError(401, "not_authenticated", REJECTED)
    from app.modules.pathways.models import CareCase

    case = db.get(CareCase, enrolment.case_id)
    return {
        "synthetic": True,
        "public_id": public_id,
        "state": case.state if case else None,
        "language": enrolment.language,
        "next_step": "Your next step is to go to the clinic.",
    }


@router.post("/talk")
def talk(data: TalkIn, public_id: str = Depends(_patient_id), db: Session = Depends(get_db)):
    enrolment = db.scalar(select(Enrolment).where(Enrolment.public_id == public_id))
    if enrolment is None:
        raise DomainError(401, "not_authenticated", REJECTED)
    result = respond(db, enrolment, data.channel, data.language, data.message)
    result["spoken_text"] = guide_speaks(result["reply_text"])
    db.commit()
    return result


@router.post("/ussd")
def ussd(data: TelegramIn, db: Session = Depends(get_db)):
    """Provider-neutral screen. The teammate's gateway calls this shape."""
    session = get_session(db, "ussd", data.chat_id)
    result = handle(db, session, data.text)
    db.commit()
    screen = ussd_contract(result["reply_text"], end=result["escalation_label"] == "danger_sign")
    screen["synthetic"] = True
    return screen


@router.get("/worklist")
def get_worklist(db: Session = Depends(get_db), user=Depends(staff)):
    return worklist.list_work(db, user)


@router.post("/worklist/{case_id}/claim")
def post_claim(case_id: int, db: Session = Depends(get_db), user=Depends(staff)):
    return worklist.claim(db, user, case_id)


@router.post("/worklist/{case_id}/attempt")
def post_attempt(case_id: int, db: Session = Depends(get_db), user=Depends(staff)):
    return worklist.log_attempt(db, user, case_id)


@router.post("/worklist/{case_id}/escalate")
def post_escalate(case_id: int, db: Session = Depends(get_db), user=Depends(staff)):
    return worklist.escalate(db, user, case_id)


@router.post("/worklist/{case_id}/outcome")
def post_outcome(case_id: int, data: OutcomeIn, db: Session = Depends(get_db), user=Depends(staff)):
    return worklist.record_outcome(db, user, case_id, data.label)


@router.get("/facility")
def get_facility(db: Session = Depends(get_db), user=Depends(facility_reader)):
    return facility.summary(db, user)


@router.get("/facility/{public_id}")
def get_timeline(public_id: str, db: Session = Depends(get_db), user=Depends(facility_reader)):
    return facility.timeline(db, user, public_id)


@router.post("/facility/{case_id}/arrive")
def post_arrive(case_id: int, db: Session = Depends(get_db), user=Depends(facility_reader)):
    case = facility.confirm_arrival(db, user, case_id)
    return {"state": case.state, "synthetic": True}


@router.post("/facility/{case_id}/care-started")
def post_care(
    case_id: int, db: Session = Depends(get_db), user=Depends(require_roles(ROLE_CLINICIAN))
):
    case = facility.care_started(db, user, case_id)
    return {"state": case.state}


@router.post("/facility/{case_id}/close")
def post_close(case_id: int, db: Session = Depends(get_db), user=Depends(facility_reader)):
    case = facility.close_with_evidence(db, user, case_id)
    return {"state": case.state}


@router.post("/facility/{case_id}/lost")
def post_lost(case_id: int, db: Session = Depends(get_db), user=Depends(facility_reader)):
    case = facility.lose(db, user, case_id)
    return {"state": case.state}


@router.post("/checkins/run")
def post_checkins(db: Session = Depends(get_db), user=Depends(require_roles(ROLE_ADMIN))):
    return {"sent": checkins.run_checkins(db), "actor": user.role}


@router.post("/telegram/webhook")
def telegram_webhook(
    data: dict,
    db: Session = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    telegram.require_signature(x_telegram_bot_api_secret_token)
    parsed = telegram.parse_update(data)
    if parsed is None:
        return {"ok": True}
    result = telegram.ingest(db, parsed)
    if not result.get("duplicate"):
        telegram.deliver(db, parsed["chat_id"], result)
    return result


@router.post("/telegram/simulate")
def telegram_sim(data: dict, db: Session = Depends(get_db)):
    parsed = telegram.parse_update(data)
    if parsed is None:
        return {"ok": True, "simulated": True}
    result = telegram.ingest(db, parsed)
    result["simulated"] = True
    return result


@router.post("/cohort")
def post_cohort(db: Session = Depends(get_db), user=Depends(require_roles(ROLE_ADMIN))):
    existing = db.scalar(select(Enrolment.id).limit(1))
    if existing:
        return report(db)
    build_cohort(db, user, 200)
    return report(db)


@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db), _user=Depends(facility_reader)):
    payload = report(db)
    payload["synthetic"] = True
    return payload
