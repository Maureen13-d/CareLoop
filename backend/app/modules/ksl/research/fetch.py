"""Download the pose dataset only after the licence gate and a checksum.

The Zenodo files are often pickled .npy arrays. This module does not load
them. Convert them in an isolated environment, then keep only plain numeric
files. Do not run that conversion inside the web server.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import tarfile
import zipfile
from collections.abc import Mapping
from pathlib import Path
from urllib.request import urlopen

from app.modules.ksl.research.policy import ResearchDisabled, dataset_config, require_license

DEST = Path("data") / "external" / "ksl_pose"


class DatasetRefused(RuntimeError):
    """Raised when a download is missing a URL, a checksum, or a safe path."""


def planned_files(config: dict, env: Mapping[str, str]) -> list[dict]:
    block = config.get("ksl_dataset") or {}
    files = [dict(item) for item in (block.get("files") or [])]
    url = env.get("KSL_DATASET_URL", "").strip() or str(block.get("download_url") or "").strip()
    digest = env.get("KSL_DATASET_SHA256", "").strip() or str(block.get("sha256") or "").strip()
    name = env.get("KSL_DATASET_FILENAME", "").strip() or "ksl_pose.zip"
    if url or digest:
        files.append({"name": name, "url": url, "sha256": digest})
    ready: list[dict] = []
    for item in files:
        item_url = str(item.get("url") or "").strip()
        item_sha = str(item.get("sha256") or "").strip().lower()
        item_name = Path(str(item.get("name") or "ksl_pose.zip")).name
        if not item_url or len(item_sha) != 64:
            raise DatasetRefused(
                "Each file needs a URL and a 64-character sha256 copied from the Zenodo record."
            )
        ready.append({"name": item_name, "url": item_url, "sha256": item_sha})
    if not ready:
        raise DatasetRefused(
            "No dataset URL or checksum. Copy both from the Zenodo record after the licence check."
        )
    return ready


def safe_relative(name: str) -> Path:
    cleaned = name.replace("\\", "/").lstrip("/")
    path = Path(cleaned)
    if not cleaned or path.is_absolute() or ".." in path.parts:
        raise DatasetRefused(f"Archive member is not a safe relative path: {name}")
    return path


def download(url: str, dest: Path, expected_sha256: str, opener=urlopen) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".partial")
    digest = hashlib.sha256()
    try:
        with opener(url) as response, partial.open("wb") as handle:
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                digest.update(block)
                handle.write(block)
        got = digest.hexdigest()
        if not hmac.compare_digest(got, expected_sha256.lower()):
            raise DatasetRefused("Checksum did not match the Zenodo record.")
        partial.replace(dest)
    finally:
        if partial.exists():
            partial.unlink()


def _is_archive(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith((".zip", ".tar", ".tar.gz", ".tgz"))


def extract(archive: Path, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    name = archive.name.lower()
    if name.endswith(".zip"):
        _extract_zip(archive, folder)
        return
    if name.endswith((".tar", ".tar.gz", ".tgz")):
        _extract_tar(archive, folder)
        return
    raise DatasetRefused("Only a zip or tar archive can be extracted.")


def _extract_zip(archive: Path, folder: Path) -> None:
    with zipfile.ZipFile(archive) as bundle:
        for info in bundle.infolist():
            relative = safe_relative(info.filename)
            target = folder / relative
            if info.is_dir() or info.filename.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(info) as source, target.open("wb") as handle:
                handle.write(source.read())


def _extract_tar(archive: Path, folder: Path) -> None:
    with tarfile.open(archive) as bundle:
        for member in bundle.getmembers():
            if member.issym() or member.islnk():
                raise DatasetRefused("Archive links are refused.")
            relative = safe_relative(member.name)
            target = folder / relative
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            source = bundle.extractfile(member)
            if source is None:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with source, target.open("wb") as handle:
                handle.write(source.read())


def run(root: Path, env: Mapping[str, str] | None = None, opener=urlopen) -> list[Path]:
    values = os.environ if env is None else env
    config = dataset_config(root / "config" / "ksl_dataset.yaml")
    require_license(config)
    files = planned_files(config, values)
    folder = root / DEST
    written: list[Path] = []
    for item in files:
        target = folder / item["name"]
        download(item["url"], target, item["sha256"], opener=opener)
        if _is_archive(target):
            extract(target, folder / "extracted")
        written.append(target)
    return written


__all__ = ["DatasetRefused", "ResearchDisabled", "planned_files", "run"]
