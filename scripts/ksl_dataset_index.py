"""Index the pose zip and count landmarks without running pickle.

The NumPy files in this dataset are object arrays. Loading them with
allow_pickle can execute code. These helpers read the zip directory and
the pickle opcodes only.
"""

from __future__ import annotations

import ast
import pickletools
import struct
from collections import Counter
from pathlib import Path

MENU = (
    "YES",
    "NO",
    "SAME",
    "BETTER",
    "WORSE",
    "HELP",
    "CLINIC",
    "HOSPITAL",
    "GO",
    "PAIN",
    "MONEY",
    "TRANSPORT",
    "AFRAID",
    "INTERPRETER",
    "REPEAT",
    "STOP",
)
CHANNELS = ("pose", "left_hand", "right_hand", "face")
_TEXT = {"SHORT_BINUNICODE", "BINUNICODE", "BINUNICODE8", "UNICODE"}


def parse_zip_index(blob: bytes) -> list[dict]:
    """Return members from a non-zip64 central directory."""
    start = blob.rfind(b"PK\x05\x06")
    if start < 0:
        raise ValueError("zip end record was not found")
    _disk, _disk2, _here, total, cd_size, cd_off, _comment = struct.unpack_from("<HHHHIIH", blob, start + 4)
    if cd_off + cd_size > len(blob):
        raise ValueError("central directory is outside this buffer")
    pos = cd_off
    end = cd_off + cd_size
    rows: list[dict] = []
    while pos + 46 <= end and blob[pos : pos + 4] == b"PK\x01\x02":
        fields = struct.unpack_from("<HHHHHHIIIHHHHHII", blob, pos + 4)
        namelen, extralen, commentlen = fields[9], fields[10], fields[11]
        name = blob[pos + 46 : pos + 46 + namelen].decode("utf-8", "replace")
        rows.append(
            {
                "name": name,
                "method": fields[3],
                "compressed_size": fields[7],
                "size": fields[8],
                "local_offset": fields[15],
            }
        )
        pos += 46 + namelen + extralen + commentlen
    if len(rows) != total:
        raise ValueError(f"expected {total} members and read {len(rows)}")
    return rows


def npy_header(raw: bytes) -> dict:
    if not raw.startswith(b"\x93NUMPY"):
        raise ValueError("not an npy file")
    major = raw[6]
    if major == 1:
        header_len = struct.unpack_from("<H", raw, 8)[0]
        text = raw[10 : 10 + header_len]
    else:
        header_len = struct.unpack_from("<I", raw, 8)[0]
        text = raw[12 : 12 + header_len]
    header = ast.literal_eval(text.decode("latin1").strip())
    if not isinstance(header, dict):
        raise ValueError("npy header was not a dict")
    return header


def npy_payload(raw: bytes) -> bytes:
    if not raw.startswith(b"\x93NUMPY"):
        raise ValueError("not an npy file")
    major = raw[6]
    if major == 1:
        header_len = struct.unpack_from("<H", raw, 8)[0]
        start = 10 + header_len
    else:
        header_len = struct.unpack_from("<I", raw, 8)[0]
        start = 12 + header_len
    return raw[start:]


def channel_counts(payload: bytes) -> list[dict[str, int]]:
    """Point counts per frame. This walks opcodes and does not unpickle.

    Later frames refer to the channel names with BINGET. Those memo ids are
    recorded when the name is first written. Coordinate tuples are not stored.
    """
    frames: list[dict[str, int]] = []
    current: dict[str, int] | None = None
    key: str | None = None
    points = 0
    memo: dict[int, str] = {}
    next_memo = 0
    pending: str | None = None

    def store_key() -> None:
        nonlocal key, points
        if current is not None and key is not None:
            current[key] = points
        key = None
        points = 0

    def use_key(name: str) -> None:
        nonlocal key, points
        store_key()
        key = name
        points = 0

    for op, arg, _pos in pickletools.genops(payload):
        if op.name in _TEXT and isinstance(arg, str):
            pending = arg if arg in CHANNELS else None
            if pending:
                use_key(pending)
            continue
        if op.name == "MEMOIZE":
            if pending:
                memo[next_memo] = pending
            pending = None
            next_memo += 1
            continue
        pending = None
        if op.name == "BINGET" and memo.get(arg) in CHANNELS:
            use_key(memo[arg])
        elif op.name == "TUPLE3" and key:
            points += 1
        elif op.name == "EMPTY_DICT":
            store_key()
            current = {}
            key = None
            points = 0
        elif op.name == "SETITEMS" and current is not None:
            store_key()
            frames.append(current)
            current = None
    return frames


def gloss(name: str) -> str:
    return Path(name.split("/")[-1]).stem.upper()


def summarise(rows: list[dict]) -> dict:
    files = [row for row in rows if not row["name"].endswith("/")]
    npy = [row for row in files if row["name"].lower().endswith(".npy")]
    mp4 = [row for row in files if row["name"].lower().endswith(".mp4")]
    words: Counter[str] = Counter()
    folders: dict[str, set[str]] = {}
    batches: Counter[str] = Counter()
    for row in npy:
        bits = row["name"].split("/")
        word = gloss(row["name"])
        folder = bits[2] if len(bits) > 2 else ""
        batch = bits[1] if len(bits) > 1 else ""
        words[word] += 1
        folders.setdefault(folder, set()).add(word)
        batches[batch] += 1
    paired = 0
    npy_keys = set()
    mp4_keys = set()
    for row in npy:
        bits = row["name"].split("/")
        if len(bits) >= 6:
            npy_keys.add((bits[1], bits[2], gloss(row["name"])))
    for row in mp4:
        bits = row["name"].split("/")
        if len(bits) >= 6:
            mp4_keys.add((bits[1], bits[2], gloss(row["name"])))
    paired = len(npy_keys & mp4_keys)
    menu = {}
    known = set(words)
    for label in MENU:
        holders = sorted(folder for folder, seen in folders.items() if label in seen)
        menu[label] = {"files": words[label], "recording_folders": holders}
    return {
        "members": len(rows),
        "npy": len(npy),
        "mp4": len(mp4),
        "directories": sum(1 for row in rows if row["name"].endswith("/")),
        "glosses": len(words),
        "recording_folders": sorted(folders),
        "batches": dict(batches),
        "paired_stickman_videos": paired,
        "menu": menu,
        "similar": _similar(known),
        "word_counts": dict(words),
    }


def _similar(known: set[str]) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for label in MENU:
        near = sorted(
            word
            for word in known
            if word != label and (word.startswith(label) or label.startswith(word)) and min(len(word), len(label)) >= 3
        )
        if near:
            found[label] = near
    return found
