"""Turn one public gloss into a research packet. The zip is not saved.

Coordinates come from a pickle opcode walk. The app never loads the .npy.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))

from app.modules.ksl.research.normalize import normalize_clip  # noqa: E402
from app.modules.ksl.research.overlay import frame_svg  # noqa: E402
from app.modules.ksl.research.policy import license_verified  # noqa: E402
from app.modules.ksl.research.publish import public_clip  # noqa: E402
from app.modules.ksl.research.retarget import retarget_clip  # noqa: E402
from inspect_ksl_dataset import load_index, member_bytes  # noqa: E402
from ksl_dataset_index import gloss, landmark_frames, npy_payload  # noqa: E402

WORD = "PAIN"
PREFERRED = "Batch 1/205"
EDGES = (
    (11, 12),
    (11, 13),
    (13, 15),
    (12, 14),
    (14, 16),
    (11, 23),
    (12, 24),
    (23, 24),
)


def choose(rows: list[dict], word: str) -> dict:
    matches = [row for row in rows if row["name"].lower().endswith(".npy") and gloss(row["name"]) == word]
    if not matches:
        raise SystemExit(f"{word} is not in the public archive index")
    for row in matches:
        if PREFERRED in row["name"]:
            return row
    return matches[0]


def sticks(frame: dict) -> list[tuple[float, float, float, float]]:
    pose = frame.get("pose") or []
    lines = []
    for start, end in EDGES:
        if start >= len(pose) or end >= len(pose):
            continue
        lines.append(
            (
                320 + pose[start][0] * 55,
                168 + pose[start][1] * 55,
                320 + pose[end][0] * 55,
                168 + pose[end][1] * 55,
            )
        )
    return lines


def main() -> int:
    if not license_verified(ROOT / "config" / "ksl_dataset.yaml"):
        print("Research mode is off. The sample is not converted.", file=sys.stderr)
        return 2
    word = sys.argv[1] if len(sys.argv) > 1 else WORD
    row = choose(load_index(), word)
    frames = landmark_frames(npy_payload(member_bytes(row)))
    packet = normalize_clip(frames, source_id=row["name"], word_label=word)
    if packet is None:
        print(f"{word} was dropped. Too many hands were missing.", file=sys.stderr)
        return 1
    public = public_clip(packet, retarget_clip(packet["frames"]))
    folder = ROOT / "data" / "external" / "ksl_pose" / "packets"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{word}.json").write_text(json.dumps(public), encoding="utf-8")
    picture = frame_svg(sticks(public["frames"][len(public["frames"]) // 2]))
    (folder / f"{word}.svg").write_text(picture, encoding="utf-8")
    print(f"wrote {word} frames={len(public['frames'])} quality={public['quality']} source={row['name']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
