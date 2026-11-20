"""Held-out danger-sign score. Do not tune the lexicon against this file."""

import json
from pathlib import Path

from app.core.config import REPO_ROOT
from app.modules.followup.conversation import classify

HELD_OUT = Path(REPO_ROOT) / "ai" / "eval" / "followup_test.jsonl"


def score_held_out(path: Path = HELD_OUT) -> dict:
    labelled = hits = 0
    misses = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row["expected"] != "danger":
            continue
        labelled += 1
        if classify(row["text"]) == "danger":
            hits += 1
        else:
            misses.append(row["id"])
    recall = round(hits / labelled, 4) if labelled else 0
    return {"n": labelled, "hits": hits, "recall": recall, "misses": misses}
