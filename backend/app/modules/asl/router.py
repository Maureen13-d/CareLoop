"""Dev playback of the small How2Sign shard. Production never serves it."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.config import REPO_ROOT

router = APIRouter(prefix="/dev/asl-research", tags=["asl-research"])
DEV_MODES = {"", "dev", "development", "demo", "test"}
SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
ASL_LABEL = "ASL RESEARCH: How2Sign sentence. Not a patient message. Not reviewed."
CITATION = (
    "Duarte et al. How2Sign: A Large-scale Multimodal Dataset for Continuous "
    "American Sign Language. CVPR 2021. Motion: How2Sign-MV3D. CC BY-NC 4.0."
)


def asl_enabled(environ: dict[str, str] | None = None) -> bool:
    values = os.environ if environ is None else environ
    return values.get("CARELOOP_ENV", "").strip().lower() in DEV_MODES


def packet_dir() -> Path:
    override = os.environ.get("ASL_RESEARCH_PACKETS", "").strip()
    if override:
        return Path(override)
    return Path(REPO_ROOT) / "data" / "external" / "asl" / "packets"


def _missing() -> None:
    raise HTTPException(status_code=404, detail="not_found")


def catalog() -> list[dict]:
    path = packet_dir() / "manifest.json"
    if not path.is_file():
        return []
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [row for row in rows if SAFE_ID.fullmatch(str(row.get("id", "")))]


@router.get("/clips")
def list_clips():
    if not asl_enabled():
        _missing()
    found = [{"id": row["id"], "sentence": row.get("sentence", "")} for row in catalog()]
    return {"clips": found, "label": ASL_LABEL, "citation": CITATION}


@router.get("/clips/{clip_id}")
def get_clip(clip_id: str):
    allowed = {row["id"] for row in catalog()}
    if not asl_enabled() or clip_id not in allowed:
        _missing()
    path = packet_dir() / f"{clip_id}.json"
    if not path.is_file():
        _missing()
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["label"] = ASL_LABEL
    payload["citation"] = CITATION
    return payload
