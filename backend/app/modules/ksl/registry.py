"""Serve a clip only when it is approved and still matches the template line."""

from __future__ import annotations

import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.ksl.kmp import blocked_in_production, source_hash
from app.modules.ksl.manifest import current_caption
from app.modules.ksl.models import KslClip, KslSigner


def production_mode(flag: bool | None = None) -> bool:
    if flag is not None:
        return flag
    return os.environ.get("CARELOOP_ENV", "").lower() == "production"


def _empty(template_id: str, caption: str) -> dict:
    return {
        "available": False,
        "template_id": template_id,
        "caption": caption,
        "fallback": "captions" if caption else "human",
        "clip_id": None,
        "video_url": None,
        "label": None,
        "pilot_enabled": False,
        "motion_uri": None,
        "icons": ["clinic"] if caption else [],
    }


def serve(db: Session, template_id: str, production: bool | None = None) -> dict:
    caption = current_caption(template_id) or ""
    base = _empty(template_id, caption)
    if not caption:
        return base
    digest = source_hash(caption)
    clips = list(db.scalars(select(KslClip).where(KslClip.template_id == template_id)).all())
    for clip in clips:
        signer = db.get(KslSigner, clip.signer_id)
        if signer and signer.consent_revoked_at is not None:
            clip.status = "retired"
            continue
        if clip.status == "approved" and clip.source_text_hash != digest:
            clip.status = "stale"
    approved = [
        clip
        for clip in clips
        if clip.status == "approved" and clip.source_text_hash == digest
    ]
    if not approved:
        return base
    clip = approved[-1]
    if blocked_in_production({"label": clip.label}, production_mode(production)):
        base["label"] = clip.label
        base["fallback"] = "captions"
        return base
    return {
        "available": True,
        "template_id": template_id,
        "caption": caption,
        "fallback": None,
        "clip_id": clip.id,
        "video_url": clip.video_uri,
        "label": clip.label,
        "pilot_enabled": bool(clip.pilot_enabled),
        "motion_uri": clip.motion_uri,
        "icons": [],
    }


def for_channel(db: Session, template_id: str, caption: str, channel: str) -> dict:
    """Web can play motion. Telegram needs a rendered video. USSD and SMS stay text."""
    served = serve(db, template_id)
    shown = caption or served["caption"]
    if channel in {"sms", "ussd"}:
        return {
            "available": False,
            "fallback": "captions" if shown else "human",
            "caption": shown,
            "icons": ["clinic"] if shown else [],
            "channel_limit": "text_only",
        }
    if channel == "telegram":
        if served["available"] and served.get("video_url"):
            return {
                "available": True,
                "clip_id": served["clip_id"],
                "fallback": None,
                "caption": shown,
                "video_url": served["video_url"],
                "label": served["label"],
                "pilot_enabled": served["pilot_enabled"],
            }
        return {
            "available": False,
            "fallback": "captions" if shown else "human",
            "caption": shown,
            "icons": ["clinic", "person"] if shown else [],
        }
    if served["available"]:
        return {
            "available": True,
            "clip_id": served["clip_id"],
            "fallback": None,
            "caption": shown,
            "video_url": served.get("video_url"),
            "label": served["label"],
            "pilot_enabled": served["pilot_enabled"],
            "motion_uri": served.get("motion_uri"),
        }
    return {
        "available": False,
        "fallback": "captions" if shown else "human",
        "caption": shown,
        "icons": ["clinic", "person"] if shown else [],
    }
