"""KSL clips, review, and the guided tap call. No free-text signing and no camera upload."""

from typing import Literal

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_roles
from app.core.errors import DomainError
from app.modules.auth.models import (
    ROLE_ADMIN,
    ROLE_CLINICIAN,
    ROLE_KSL_REVIEWER,
    ROLE_NAVIGATOR,
    ROLE_PROGRAM_MANAGER,
)
from app.modules.followup import voice
from app.modules.followup.access import REJECTED, read_token
from app.modules.followup.conversation import guide_speaks, respond
from app.modules.followup.models import Enrolment
from app.modules.ksl import registry, review
from app.modules.ksl.guided import GuidedCall
from app.modules.ksl.models import KslClip, KslSigner
from app.modules.tasks.models import NavigatorTask

router = APIRouter(prefix="/ksl", tags=["ksl"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
staff = require_roles(ROLE_ADMIN, ROLE_PROGRAM_MANAGER, ROLE_KSL_REVIEWER, ROLE_NAVIGATOR, ROLE_CLINICIAN)
editors = require_roles(ROLE_ADMIN, ROLE_PROGRAM_MANAGER)
reviewers = require_roles(ROLE_KSL_REVIEWER)

_calls: dict[str, GuidedCall] = {}
TALK = {
    "yes": "been",
    "no": "not yet",
    "same": "same",
    "better": "better",
    "worse": "worse",
    "cant_go": "cant go",
    "need_interpreter": "need interpreter",
    "need_help": "need help",
    "stop": "stop",
}


class SignerIn(BaseModel):
    pseudonym: str = Field(min_length=2, max_length=80)


class ClipIn(BaseModel):
    template_id: str
    signer_id: int
    label: str = Field(min_length=2, max_length=80)
    motion_uri: str = Field(min_length=3, max_length=300)
    video_uri: str | None = None


class ReviewIn(BaseModel):
    kind: Literal["deaf_review", "back_translation"]
    result: Literal["pass", "fail"]


class FlagIn(BaseModel):
    interpreter_available: bool
    recorded_on: str


class TalkIn(BaseModel):
    message: str = ""
    channel: Literal["web", "telegram", "sms", "ussd"] = "web"
    speak: bool = False


class GuidedIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["tap", "confirm", "consent"]
    choice: str = ""
    yes: bool = False


def reset_calls() -> None:
    _calls.clear()


def _patient_id(token: str | None = Depends(oauth2_scheme)) -> str:
    public_id = read_token(token)
    if not public_id:
        raise DomainError(401, "not_authenticated", REJECTED)
    return public_id


def _clip_out(clip: KslClip) -> dict:
    return {
        "id": clip.id,
        "template_id": clip.template_id,
        "label": clip.label,
        "status": clip.status,
        "pilot_enabled": clip.pilot_enabled,
        "video_uri": clip.video_uri,
    }


@router.get("/clip/{template_id}")
def get_clip(template_id: str, db: Session = Depends(get_db)):
    return registry.serve(db, template_id)


@router.get("/clips")
def list_clips(db: Session = Depends(get_db), _user=Depends(staff)):
    rows = db.scalars(select(KslClip).order_by(KslClip.id)).all()
    return [_clip_out(row) for row in rows]


@router.post("/signers", status_code=201)
def post_signer(data: SignerIn, db: Session = Depends(get_db), user=Depends(editors)):
    signer = review.add_signer(db, user, data.pseudonym)
    db.commit()
    return {"id": signer.id, "pseudonym": signer.pseudonym}


@router.post("/clips", status_code=201)
def post_clip(data: ClipIn, db: Session = Depends(get_db), user=Depends(editors)):
    clip = review.upload_clip(
        db,
        user,
        template_id=data.template_id,
        signer_id=data.signer_id,
        label=data.label,
        motion_uri=data.motion_uri,
        video_uri=data.video_uri,
    )
    db.commit()
    return _clip_out(clip)


@router.post("/clips/{clip_id}/reviews", status_code=201)
def post_review(clip_id: int, data: ReviewIn, db: Session = Depends(get_db), user=Depends(reviewers)):
    clip = db.get(KslClip, clip_id)
    if clip is None:
        raise DomainError(404, "not_found", "Clip was not found")
    row = review.add_review(db, user, clip, data.kind, data.result)
    db.commit()
    return {"id": row.id, "kind": row.kind, "result": row.result}


@router.post("/clips/{clip_id}/approve")
def post_approve(clip_id: int, db: Session = Depends(get_db), user=Depends(editors)):
    clip = db.get(KslClip, clip_id)
    if clip is None:
        raise DomainError(404, "not_found", "Clip was not found")
    review.approve(db, user, clip)
    db.commit()
    return _clip_out(clip)


@router.post("/signers/{signer_id}/revoke")
def post_revoke(signer_id: int, db: Session = Depends(get_db), user=Depends(editors)):
    signer = db.get(KslSigner, signer_id)
    if signer is None:
        raise DomainError(404, "not_found", "Signer was not found")
    retired = review.revoke_signer(db, user, signer)
    db.commit()
    return {"id": signer.id, "retired": retired}


@router.post("/facilities/{facility_key}/interpreter")
def post_flag(
    facility_key: str,
    data: FlagIn,
    db: Session = Depends(get_db),
    user=Depends(require_roles(ROLE_ADMIN, ROLE_PROGRAM_MANAGER, ROLE_NAVIGATOR, ROLE_CLINICIAN)),
):
    row = review.set_facility_flag(
        db, user, facility_key, data.interpreter_available, data.recorded_on
    )
    db.commit()
    return {
        "facility_key": row.facility_key,
        "interpreter_available": row.interpreter_available,
        "recorded_on": row.recorded_on,
    }


@router.post("/talk")
def talk(data: TalkIn, public_id: str = Depends(_patient_id), db: Session = Depends(get_db)):
    enrolment = db.scalar(select(Enrolment).where(Enrolment.public_id == public_id))
    if enrolment is None:
        raise DomainError(401, "not_authenticated", REJECTED)
    enrolment.language = "ksl"
    result = respond(db, enrolment, data.channel, "ksl", data.message)
    result["spoken_text"] = guide_speaks(result["reply_text"])
    if data.speak:
        voice.speak_reply(result)
    db.commit()
    return result


def _open_tasks(db: Session, case_id: int | None) -> int:
    if case_id is None:
        return 0
    return int(
        db.scalar(
            select(func.count())
            .select_from(NavigatorTask)
            .where(NavigatorTask.case_id == case_id, NavigatorTask.status == "open")
        )
        or 0
    )


@router.post("/guided")
def post_guided(data: GuidedIn, public_id: str = Depends(_patient_id), db: Session = Depends(get_db)):
    enrolment = db.scalar(select(Enrolment).where(Enrolment.public_id == public_id))
    if enrolment is None:
        raise DomainError(401, "not_authenticated", REJECTED)
    enrolment.language = "ksl"
    call = _calls.setdefault(public_id, GuidedCall())
    before = _open_tasks(db, enrolment.case_id)
    if data.action == "consent":
        view = call.consent(False)
    elif data.action == "confirm":
        view = call.confirm(data.yes)
    else:
        view = call.tap(data.choice)
    reply = None
    if view["committed"] and data.action == "confirm" and data.yes:
        message = TALK.get(view["committed"], "")
        if message:
            reply = respond(db, enrolment, "web", "ksl", message)
    if view["committed"] == "stop" and data.action == "tap":
        reply = respond(db, enrolment, "web", "ksl", "stop")
    db.commit()
    opened = _open_tasks(db, enrolment.case_id) - before
    return {
        **view,
        "reply_text": None if reply is None else reply["reply_text"],
        "template_id": None if reply is None else reply.get("template_id"),
        "ksl": None if reply is None else reply.get("ksl"),
        "tasks_opened": opened,
    }
