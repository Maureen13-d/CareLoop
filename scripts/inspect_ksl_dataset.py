"""Inspect the open Zenodo zip by range request. Do not save the archive.

The latest cited record, 10.5281/zenodo.14974973, is restricted and has no
public files. The open file is version 10.5281/zenodo.14338329. Landmark
files are object arrays, so this script never calls pickle.loads.
"""

from __future__ import annotations

import json
import struct
import sys
import urllib.request
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "scripts"))

from app.modules.ksl.research.policy import license_verified  # noqa: E402
from ksl_dataset_index import (  # noqa: E402
    MENU,
    channel_counts,
    gloss,
    npy_header,
    npy_payload,
    parse_zip_index,
    summarise,
)

URL = "https://zenodo.org/api/records/14338329/files/Pose%20Data.zip/content"
RECORD_SIZE = 1539828602


def fetch(start: int, end: int) -> bytes:
    last_error: Exception | None = None
    for _attempt in range(4):
        request = urllib.request.Request(
            URL,
            headers={"User-Agent": "CareLoop-research/0.1", "Range": f"bytes={start}-{end}"},
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                return response.read()
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"range {start}-{end} failed") from last_error


def load_index() -> list[dict]:
    tail = fetch(RECORD_SIZE - 80, RECORD_SIZE - 1)
    start = tail.rfind(b"PK\x05\x06")
    _disk, _disk2, _here, _total, cd_size, cd_off, _comment = struct.unpack_from("<HHHHIIH", tail, start + 4)
    directory = fetch(cd_off, cd_off + cd_size - 1)
    # The parser expects the end record after the directory when given a whole zip.
    # Build a buffer that contains the directory at its real offset by attaching a
    # matching end record, so a partial download is enough.
    blob = directory + tail[start:]
    patched = bytearray(blob)
    struct.pack_into("<I", patched, len(directory) + 16, 0)
    return parse_zip_index(bytes(patched))


def member_bytes(row: dict) -> bytes:
    local = row["local_offset"]
    head = fetch(local, local + 511)
    if head[:4] != b"PK\x03\x04":
        raise ValueError(f"local header missing for {row['name']}")
    name_len, extra_len = struct.unpack_from("<HH", head, 26)
    data_at = local + 30 + name_len + extra_len
    compressed = fetch(data_at, data_at + row["compressed_size"] - 1)
    if row["method"] == 8:
        return zlib.decompress(compressed, -15)
    if row["method"] == 0:
        return compressed
    raise ValueError(f"unsupported compression {row['method']}")


def sample_menu(rows: list[dict]) -> dict:
    """Read the first file of each exact menu label. Opcodes only, no unpickle."""
    wanted: dict[str, dict] = {}
    for row in rows:
        if not row["name"].lower().endswith(".npy"):
            continue
        label = gloss(row["name"])
        if label not in MENU or label in wanted:
            continue
        try:
            raw = member_bytes(row)
            header = npy_header(raw)
            counts = channel_counts(npy_payload(raw))
        except Exception as exc:
            wanted[label] = {"name": row["name"], "error": str(exc)}
            continue
        empty = {channel: 0 for channel in ("pose", "left_hand", "right_hand", "face")}
        for frame in counts:
            for channel, points in frame.items():
                if points == 0:
                    empty[channel] += 1
        wanted[label] = {
            "name": row["name"],
            "shape": list(header.get("shape") or []),
            "descr": str(header.get("descr")),
            "frames": len(counts),
            "empty_frames": empty,
            "first_frame_points": counts[0] if counts else {},
        }
    return wanted


def main() -> int:
    if not license_verified(ROOT / "config" / "ksl_dataset.yaml"):
        print("Research mode is off. The inspection does not run.", file=sys.stderr)
        return 2
    rows = load_index()
    report = summarise(rows)
    report["samples"] = sample_menu(rows)
    text = json.dumps(report, indent=2) + "\n"
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
