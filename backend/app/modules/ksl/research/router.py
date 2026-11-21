"""Dev-only playback of one research word. Production and patients never see it."""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.config import REPO_ROOT
from app.modules.ksl.research.overlay import CITATION, RESEARCH_LABEL
from app.modules.ksl.research.policy import license_verified

router = APIRouter(prefix="/dev/ksl-research", tags=["ksl-research"])
SHORTLIST = ("GO", "HELP", "SAME", "NO", "STOP", "PAIN", "MONEY")
DEV_MODES = {"", "dev", "development", "demo", "test"}
PLAYBACK_FPS = 12


def research_enabled(environ: dict[str, str] | None = None) -> bool:
    values = os.environ if environ is None else environ
    mode = values.get("CARELOOP_ENV", "").strip().lower()
    if mode not in DEV_MODES:
        return False
    return license_verified()


def packet_dir() -> Path:
    override = os.environ.get("KSL_RESEARCH_PACKETS", "").strip()
    if override:
        return Path(override)
    return Path(REPO_ROOT) / "data" / "external" / "ksl_pose" / "packets"


def _missing() -> None:
    raise HTTPException(status_code=404, detail="not_found")


@router.get("/words")
def list_words():
    if not research_enabled():
        _missing()
    found = [word for word in SHORTLIST if (packet_dir() / f"{word}.json").is_file()]
    return {
        "words": found,
        "label": RESEARCH_LABEL,
        "citation": CITATION,
        "playback_fps": PLAYBACK_FPS,
        "fps_from_dataset": None,
    }


@router.get("/words/{word}")
def get_word(word: str):
    if not research_enabled() or word not in SHORTLIST:
        _missing()
    path = packet_dir() / f"{word}.json"
    if not path.is_file():
        _missing()
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["label"] = RESEARCH_LABEL
    payload["citation"] = CITATION
    return payload
