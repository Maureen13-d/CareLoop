"""Held-out maternal companion scores. Synthetic messages only.

The lexicon is not edited from this output.
"""

import json
from pathlib import Path

from app.core.config import REPO_ROOT
from app.modules.assistant.schemas import AssistantRequest
from app.modules.maternal.companion import handle_maternal

LABELS = ("red", "yellow", "green", "crisis", "distress")


def classify(text: str) -> str:
    response = handle_maternal(
        AssistantRequest(channel="sms", pathway="maternal", text=text, language="en")
    )
    for name in LABELS:
        if f".{name}." in response.template_id:
            return name
    return "unclear"


def load_rows(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def score(path: Path) -> dict:
    rows = load_rows(path)
    misses = []
    predicted_red = 0
    labelled_red = 0
    red_hits = 0
    false_red = 0
    non_red = 0
    correct = 0
    for row in rows:
        got = classify(row["text"])
        expected = row["label"]
        if got == expected:
            correct += 1
        else:
            misses.append({"id": row["id"], "expected": expected, "predicted": got, "text": row["text"]})
        if expected == "red":
            labelled_red += 1
            if got == "red":
                red_hits += 1
        else:
            non_red += 1
            if got == "red":
                false_red += 1
        if got == "red":
            predicted_red += 1
    return {
        "n": len(rows),
        "accuracy": round(correct / len(rows), 4) if rows else 0,
        "correct": correct,
        "red_recall": round(red_hits / labelled_red, 4) if labelled_red else 0,
        "red_hits": red_hits,
        "labelled_red": labelled_red,
        "false_alarm_rate": round(false_red / non_red, 4) if non_red else 0,
        "false_red": false_red,
        "non_red": non_red,
        "predicted_red": predicted_red,
        "misses": misses,
        "note": "Synthetic messages only. Not clinical validation.",
    }


def main() -> None:
    path = REPO_ROOT / "ai" / "eval" / "maternal_test.jsonl"
    print(json.dumps(score(path), indent=2))


if __name__ == "__main__":
    main()
