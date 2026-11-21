"""Reject raw KSL footage and oversized binaries that are tracked in git.

Raw video, raw mocap, and signer photos do not belong in this repository.
Approved derived packs may be Git LFS pointers under assets/ksl/approved/.
Small synthetic motion may live under assets/ksl/placeholders/ and must stay under 200 KB.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

VIDEO = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".wmv",
    ".m4v",
    ".mpg",
    ".mpeg",
    ".3gp",
}
MOCAP = {".bvh", ".c3d", ".fbx", ".trc"}
SIGNER_PHOTO = {".jpg", ".jpeg", ".heic", ".heif", ".tif", ".tiff", ".png", ".gif", ".webp"}
RAW_PARTS = {"capture", "raw_mocap", "signer_photos", "signer_footage"}

PLACEHOLDERS = "assets/ksl/placeholders/"
APPROVED = "assets/ksl/approved/"
RENDERED = {".mp4", ".webm"}
MAX_BYTES = 3 * 1024 * 1024
PLACEHOLDER_MAX = 200 * 1024
LFS_MARK = b"version https://git-lfs.github.com/spec/v1"


def reasons(rel: str, size: int, head: bytes) -> list[str]:
    """Return why this tracked path is not allowed. Empty means it may stay."""
    rel = rel.replace("\\", "/")
    ext = Path(rel).suffix.lower()
    parts = set(Path(rel).parts)
    found: list[str] = []
    if parts & RAW_PARTS:
        found.append("raw capture path")
    if ext in MOCAP:
        found.append("raw mocap")
    if rel.startswith("assets/ksl/") and ext in SIGNER_PHOTO:
        found.append("signer photo")
    if ext in VIDEO and not rel.startswith(APPROVED):
        found.append("video outside approved packs")
    if ext in VIDEO and rel.startswith(APPROVED):
        if ext not in RENDERED:
            found.append("camera video is not an approved pack")
        elif not head.startswith(LFS_MARK):
            found.append("approved video must be a Git LFS pointer")
    if rel.startswith(PLACEHOLDERS):
        if ext in VIDEO | MOCAP | SIGNER_PHOTO:
            found.append("placeholder folder is for small motion files only")
        if size > PLACEHOLDER_MAX:
            found.append("placeholder over 200 KB")
    elif size > MAX_BYTES and not head.startswith(LFS_MARK):
        found.append("file over 3 MB and not a Git LFS pointer")
    return found


def tracked_files(root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    text = completed.stdout.decode("utf-8")
    return [name for name in text.split("\0") if name]


def scan(root: Path) -> list[str]:
    problems: list[str] = []
    for rel in tracked_files(root):
        path = root / rel
        if not path.is_file():
            continue
        size = path.stat().st_size
        with path.open("rb") as handle:
            head = handle.read(len(LFS_MARK))
        for reason in reasons(rel, size, head):
            problems.append(f"{rel}: {reason}")
    return problems


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    problems = scan(root)
    if problems:
        print("KSL asset policy failed:", file=sys.stderr)
        for line in problems:
            print(line, file=sys.stderr)
        return 1
    print("KSL asset policy passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
