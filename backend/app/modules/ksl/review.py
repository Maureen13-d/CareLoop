"""Two Deaf passes, then a different person confirms. Pending clinical lines stay off for pilots."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.errors import DomainError
from app.modules.audit import service as audit
from app.modules.auth.models import ROLE_ADMIN, ROLE_KSL_REVIEWER, ROLE_PROGRAM_MANAGER
from app.modules.ksl.kmp import source_hash
from app.modules.ksl.manifest import current_caption, phrase_by_id
from app.modules.ksl.models import KslClip, KslFacilityFlag, KslReview, KslSigner

REVIEW_KINDS = {"deaf_review", "back_translation"}
APPROVERS = {ROLE_ADMIN, ROLE_PROGRAM_MANAGER}


def add_signer(db: Session, actor, pseudonym: str) -> KslSigner:
    if actor.role not in APPROVERS:
        raise DomainError(403, "forbidden", "Role is not allowed to record consent")
    signer = KslSigner(pseudonym=pseudonym.strip(), consent_recorded_at=clock.now())
    db.add(signer)
    db.flush()
    audit.record(
        db,
        actor=actor,
        action="ksl.signer_recorded",
        entity_type="ksl_signer",
        entity_id=signer.id,
        detail={"label": "consent_recorded"},
    )
    return signer


def upload_clip(
    db: Session,
    actor,
    *,
    template_id: str,
    signer_id: int,
    label: str,
    motion_uri: str,
    video_uri: str | None = None,
) -> KslClip:
    if actor.role not in APPROVERS:
        raise DomainError(403, "forbidden", "Role is not allowed to upload a clip")
    caption = current_caption(template_id)
    if not caption:
        raise DomainError(400, "unknown_phrase", "That phrase is not in the manifest")
    signer = db.get(KslSigner, signer_id)
    if signer is None or signer.consent_revoked_at is not None:
        raise DomainError(400, "no_consent", "That signer has no active consent")
    clip = KslClip(
        template_id=template_id,
        source_text_hash=source_hash(caption),
        signer_id=signer.id,
        label=label.strip(),
        status="uploaded",
        pilot_enabled=False,
        motion_uri=motion_uri,
        video_uri=video_uri,
        uploaded_by_id=actor.id,
        created_at=clock.now(),
    )
    db.add(clip)
    db.flush()
    audit.record(
        db,
        actor=actor,
        action="ksl.clip_uploaded",
        entity_type="ksl_clip",
        entity_id=clip.id,
        detail={"label": template_id},
    )
    return clip


def add_review(db: Session, actor, clip: KslClip, kind: str, result: str) -> KslReview:
    if actor.role != ROLE_KSL_REVIEWER:
        raise DomainError(403, "forbidden", "A Deaf reviewer records this pass")
    if kind not in REVIEW_KINDS or result not in {"pass", "fail"}:
        raise DomainError(400, "bad_review", "Review kind was not accepted")
    if actor.id == clip.uploaded_by_id:
        raise DomainError(403, "forbidden", "The uploader cannot review their own clip")
    already = db.scalar(
        select(KslReview).where(KslReview.clip_id == clip.id, KslReview.reviewer_id == actor.id)
    )
    if already is not None:
        raise DomainError(409, "not_ready", "A reviewer records one pass")
    if kind == "back_translation":
        deaf = db.scalars(
            select(KslReview).where(
                KslReview.clip_id == clip.id,
                KslReview.kind == "deaf_review",
                KslReview.result == "pass",
                KslReview.reviewer_id == actor.id,
            )
        ).first()
        if deaf is not None:
            raise DomainError(409, "not_ready", "Back-translation needs a second Deaf reviewer")
    row = KslReview(
        clip_id=clip.id,
        reviewer_id=actor.id,
        kind=kind,
        result=result,
        created_at=clock.now(),
    )
    db.add(row)
    db.flush()
    audit.record(
        db,
        actor=actor,
        action="ksl.review",
        entity_type="ksl_clip",
        entity_id=clip.id,
        detail={"label": kind, "result": result},
    )
    return row


def approve(db: Session, actor, clip: KslClip) -> KslClip:
    if actor.role not in APPROVERS:
        raise DomainError(403, "forbidden", "Role is not allowed to approve a clip")
    if actor.id == clip.uploaded_by_id:
        raise DomainError(403, "forbidden", "The approver cannot be the uploader")
    reviews = list(db.scalars(select(KslReview).where(KslReview.clip_id == clip.id)).all())
    deaf_ids = {row.reviewer_id for row in reviews if row.kind == "deaf_review" and row.result == "pass"}
    back_ids = {
        row.reviewer_id for row in reviews if row.kind == "back_translation" and row.result == "pass"
    }
    if not deaf_ids or not (back_ids - deaf_ids):
        raise DomainError(409, "not_ready", "A Deaf review and a second back-translation are required")
    if actor.id in deaf_ids | back_ids:
        raise DomainError(403, "forbidden", "The approver cannot be one of the reviewers")
    item = phrase_by_id(clip.template_id) or {}
    clip.status = "approved"
    clip.approved_at = clock.now()
    clip.approved_by_id = actor.id
    clip.pilot_enabled = item.get("clinical_review") == "reviewed"
    audit.record(
        db,
        actor=actor,
        action="ksl.clip_approved",
        entity_type="ksl_clip",
        entity_id=clip.id,
        detail={"label": clip.template_id, "pilot_enabled": clip.pilot_enabled},
    )
    return clip


def revoke_signer(db: Session, actor, signer: KslSigner) -> int:
    if actor.role not in APPROVERS:
        raise DomainError(403, "forbidden", "Role is not allowed to revoke consent")
    signer.consent_revoked_at = clock.now()
    clips = list(db.scalars(select(KslClip).where(KslClip.signer_id == signer.id)).all())
    for clip in clips:
        clip.status = "retired"
    audit.record(
        db,
        actor=actor,
        action="ksl.consent_revoked",
        entity_type="ksl_signer",
        entity_id=signer.id,
        detail={"label": "revoked", "clips": len(clips)},
    )
    return len(clips)


def set_facility_flag(db: Session, actor, facility_key: str, available: bool, recorded_on: str) -> KslFacilityFlag:
    if actor.role not in APPROVERS | {"navigator", "clinician"}:
        raise DomainError(403, "forbidden", "Role is not allowed to record this flag")
    if len(recorded_on) != 10 or recorded_on[4] != "-" or recorded_on[7] != "-":
        raise DomainError(400, "bad_date", "Record the date as YYYY-MM-DD")
    row = db.scalar(select(KslFacilityFlag).where(KslFacilityFlag.facility_key == facility_key))
    if row is None:
        row = KslFacilityFlag(
            facility_key=facility_key,
            interpreter_available=available,
            recorded_on=recorded_on,
        )
        db.add(row)
    else:
        row.interpreter_available = available
        row.recorded_on = recorded_on
    db.flush()
    audit.record(
        db,
        actor=actor,
        action="ksl.facility_flag",
        entity_type="ksl_facility",
        entity_id=row.id,
        detail={"label": "interpreter" if available else "no_interpreter", "recorded_on": recorded_on},
    )
    return row
