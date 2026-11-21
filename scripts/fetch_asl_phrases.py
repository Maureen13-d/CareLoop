"""Stream How2Sign-MV3D archives and keep a few real sentences.

The archives are about 1GB. This script does not write the archive. It reads
the tar stream, saves only the named clips as JSON, and stops each archive
once those clips are found.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ASL = ROOT / "data" / "external" / "asl"
OUT = ASL / "packets"
BASE = "https://huggingface.co/datasets/mage0001/How2Sign-MV3D/resolve/main/"

# Real How2Sign lines. The English is what the signer said.
PICKS = {
    "--8pSDeC-fg_0-5": "data/train-00000.tar",
    "1xKU91ggLeI_2-5": "data/train-00000.tar",
    "--8pSDeC-fg_7-5": "data/train-00006.tar",
    "--8pSDeC-fg_1-5": "data/train-00001.tar",
    "g1HXoDkax5A_20-3": "data/test-00000.tar",
    "-0N0jbyBW6g_11-5": "data/train-00000.tar",
    "-F6vN4bOBWs_16-8": "data/train-00000.tar",
}
ORDER = list(PICKS)


class Reader:
    def __init__(self, response) -> None:
        self.response = response
        self.buf = b""
        self.offset = 0

    def read(self, count: int) -> bytes:
        while len(self.buf) < count:
            chunk = self.response.read(1024 * 1024)
            if not chunk:
                break
            self.buf += chunk
        data = self.buf[:count]
        self.buf = self.buf[count:]
        self.offset += len(data)
        return data


def sentences() -> dict[str, str]:
    text: dict[str, str] = {}
    for path in (ASL / "how2sign_test_sentences.csv", ASL / "how2sign_train_sentences.csv"):
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines()[1:]:
            parts = line.split("\t")
            if len(parts) < 7:
                continue
            name = parts[3].replace("-rgb_front", "").replace("-rgb_side", "")
            text[name] = parts[6]
    return text


def open_tar(archive: str, start: int) -> Reader:
    headers = {"User-Agent": "CareLoop-research/0.1"}
    if start:
        headers["Range"] = f"bytes={start}-"
    request = urllib.request.Request(BASE + archive, headers=headers)
    response = urllib.request.urlopen(request, timeout=180)
    if start and getattr(response, "status", 200) != 206:
        raise RuntimeError(f"{archive} did not resume at {start}")
    reader = Reader(response)
    reader.offset = start
    return reader


def header_name(header: bytes) -> tuple[str, int, bytes]:
    name = header[0:100].split(b"\0", 1)[0].decode("utf-8", "replace")
    size = int(header[124:136].split(b"\0", 1)[0].strip() or b"0", 8)
    return name, size, header[156:157]


def packet(sample_id: str, blob: bytes, text: dict[str, str], source: str) -> dict:
    path = OUT / "_one.npz"
    path.write_bytes(blob)
    with np.load(path, allow_pickle=False) as loaded:
        proj = loaded["smplx_joint_proj"][:, :55].copy()
        hands = loaded["wilor_hand_valid_mask"].copy()
        fps = float(loaded["mocap_framerate"])
        stored = str(loaded["sample_id"])
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
        "id": stored or sample_id,
        "sentence": text.get(sample_id) or text.get(stored, ""),
        "sample_id": stored or sample_id,
        "fps": fps,
        "source": source,
        "license": "CC BY-NC 4.0",
        "frames": frames,
    }


def remember(body: dict) -> None:
    manifest_path = OUT / "manifest.json"
    rows = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else []
    rows = [row for row in rows if row.get("id") != body["id"]]
    rows.append({"id": body["id"], "sentence": body["sentence"], "frames": len(body["frames"])})
    front = []
    for sample_id in ORDER:
        match = next((row for row in rows if row["id"] == sample_id), None)
        if match:
            front.append(match)
    rest = [row for row in rows if row["id"] not in ORDER]
    rest.sort(key=lambda row: row["sentence"].lower())
    manifest_path.write_text(json.dumps(front + rest), encoding="utf-8")


def take(archive: str, wanted: set[str], text: dict[str, str]) -> None:
    wanted = {sample_id for sample_id in wanted if not (OUT / f"{sample_id}.json").is_file()}
    print(f"stream {archive} for {sorted(wanted)}", flush=True)
    resume = 0
    pending_name = ""
    attempts = 0
    while wanted and attempts < 24:
        try:
            reader = open_tar(archive, resume)
            print(f"  open at {resume // (1024 * 1024)}MB", flush=True)
            while wanted:
                header = reader.read(512)
                if len(header) < 512:
                    raise ConnectionError("short header")
                if header[0:4] == b"\0\0\0\0":
                    print(f"  end at {reader.offset // (1024 * 1024)}MB", flush=True)
                    return
                name, size, kind = header_name(header)
                if size > 30_000_000:
                    raise RuntimeError(f"bad member size {size} at {resume}")
                pad = (512 - (size % 512)) % 512
                blob = reader.read(size + pad)
                data = blob[:size]
                resume = reader.offset
                if kind == b"L":
                    pending_name = data.split(b"\0", 1)[0].decode("utf-8", "replace")
                    continue
                if pending_name:
                    name = pending_name
                    pending_name = ""
                sample_id = Path(name).stem
                if resume % (80 * 1024 * 1024) < size + pad + 512:
                    print(f"  {resume // (1024 * 1024)}MB {name}", flush=True)
                if sample_id not in wanted:
                    continue
                body = packet(sample_id, data, text, f"How2Sign-MV3D {archive} {name}")
                (OUT / f"{body['id']}.json").write_text(
                    json.dumps(body, separators=(",", ":")),
                    encoding="utf-8",
                )
                remember(body)
                wanted.remove(sample_id)
                print(f"kept {body['id']} {len(body['frames'])}f {body['sentence']}", flush=True)
        except Exception as exc:
            attempts += 1
            pending_name = ""
            print(f"retry {attempts} at {resume} after {exc.__class__.__name__}", flush=True)
    missing = ", ".join(sorted(wanted))
    print(f"done {archive} missing={missing or 'none'}", flush=True)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    text = sentences()
    by_archive: dict[str, set[str]] = {}
    for sample_id, archive in PICKS.items():
        by_archive.setdefault(archive, set()).add(sample_id)
    for archive, wanted in by_archive.items():
        take(archive, wanted, text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
