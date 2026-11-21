"""Save every sentence in the small How2Sign-MV3D test shard.

The shard is about 50MB. The other archives are about 1GB each and are not
downloaded. Numpy stays in this script. The web app reads the JSON only.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ASL = ROOT / "data" / "external" / "asl"
OUT = ASL / "packets"
TAR_URL = "https://huggingface.co/datasets/mage0001/How2Sign-MV3D/resolve/main/data/test-00001.tar"
TAR_SIZE = 52_193_280


def fetch(start: int, end: int) -> bytes:
    last_error: Exception | None = None
    for _attempt in range(4):
        request = urllib.request.Request(
            TAR_URL,
            headers={"User-Agent": "CareLoop-research/0.1", "Range": f"bytes={start}-{end}"},
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                return response.read()
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"range {start}-{end} failed") from last_error


def sentences() -> dict[str, str]:
    text: dict[str, str] = {}
    for line in (ASL / "how2sign_test_sentences.csv").read_text(encoding="utf-8").splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        name = parts[3].replace("-rgb_front", "").replace("-rgb_side", "")
        text[name] = parts[6]
    return text


def members() -> list[tuple[str, int, int]]:
    found = []
    offset = 0
    while offset + 512 <= TAR_SIZE:
        header = fetch(offset, offset + 511)
        if header[0:4] == b"\0\0\0\0":
            break
        name = header[0:100].split(b"\0", 1)[0].decode("utf-8", "replace")
        size = int(header[124:136].split(b"\0", 1)[0].strip() or b"0", 8)
        data_at = offset + 512
        if name.endswith(".npz") and size:
            found.append((name, data_at, size))
        offset = data_at + ((size + 511) // 512) * 512
    return found


def packet(name: str, blob: bytes, text: dict[str, str]) -> dict:
    path = OUT / "_one.npz"
    path.write_bytes(blob)
    with np.load(path, allow_pickle=False) as loaded:
        sample_id = str(loaded["sample_id"])
        proj = loaded["smplx_joint_proj"][:, :55].copy()
        hands = loaded["wilor_hand_valid_mask"].copy()
        fps = float(loaded["mocap_framerate"])
    path.unlink(missing_ok=True)
    frames = []
    for index in range(proj.shape[0]):
        frames.append(
            {
                "proj": [[round(float(point[0]), 1), round(float(point[1]), 1)] for point in proj[index]],
                "left_hand": bool(hands[index, 0]),
                "right_hand": bool(hands[index, 1]),
            }
        )
    return {
        "id": sample_id,
        "sentence": text.get(sample_id, ""),
        "sample_id": sample_id,
        "fps": fps,
        "source": f"How2Sign-MV3D {name}",
        "license": "CC BY-NC 4.0",
        "frames": frames,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob("*.json"):
        stale.unlink()
    text = sentences()
    rows = []
    for name, data_at, size in members():
        body = packet(name, fetch(data_at, data_at + size - 1), text)
        (OUT / f"{body['id']}.json").write_text(json.dumps(body, separators=(",", ":")), encoding="utf-8")
        rows.append({"id": body["id"], "sentence": body["sentence"], "frames": len(body["frames"])})
        print(f"{len(body['frames']):4} {body['sentence'][:80]}", flush=True)
    rows.sort(key=lambda row: row["sentence"].lower())
    (OUT / "manifest.json").write_text(json.dumps(rows), encoding="utf-8")
    print(f"sentences {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
