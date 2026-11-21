"""Download the pose dataset only after the licence gate and a checksum.

The Zenodo files are often pickled .npy arrays. This module does not load
them. Convert them in an isolated environment, then keep only plain numeric
files. Do not run that conversion inside the web server.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import shutil
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
    md5 = env.get("KSL_DATASET_MD5", "").strip() or str(block.get("md5") or "").strip()
    name = env.get("KSL_DATASET_FILENAME", "").strip() or "ksl_pose.zip"
    if url or digest or md5:
        files.append({"name": name, "url": url, "sha256": digest, "md5": md5})
    ready: list[dict] = []
    for item in files:
        item_url = str(item.get("url") or "").strip()
        item_sha = str(item.get("sha256") or "").strip().lower()
        item_md5 = str(item.get("md5") or "").strip().lower()
        item_name = Path(str(item.get("name") or "ksl_pose.zip")).name
        if not item_url or (len(item_sha) != 64 and len(item_md5) != 32):
            raise DatasetRefused(
                "Each file needs a URL and a checksum copied from the Zenodo record."
            )
        ready.append({"name": item_name, "url": item_url, "sha256": item_sha, "md5": item_md5})
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


def download(
    url: str,
    dest: Path,
    expected_sha256: str = "",
    opener=urlopen,
    expected_md5: str = "",
    free_bytes: int | None = None,
) -> None:
    if not expected_sha256 and not expected_md5:
        raise DatasetRefused("A checksum from the Zenodo record is required.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".partial")
    digest = hashlib.sha256()
    md5 = hashlib.md5()
    try:
        with opener(url) as response:
            headers = getattr(response, "headers", None)
            length = headers.get("Content-Length") if headers is not None else None
            if length:
                needed = int(length)
                free = shutil.disk_usage(dest.parent).free if free_bytes is None else free_bytes
                if needed > free:
                    raise DatasetRefused("Not enough free disk to keep this file.")
            with partial.open("wb") as handle:
                while True:
                    block = response.read(1024 * 1024)
                    if not block:
                        break
                    digest.update(block)
                    md5.update(block)
                    handle.write(block)
        if expected_sha256 and not hmac.compare_digest(digest.hexdigest(), expected_sha256.lower()):
            raise DatasetRefused("Checksum did not match the Zenodo record.")
        if expected_md5 and not hmac.compare_digest(md5.hexdigest(), expected_md5.lower()):
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
        download(
            item["url"],
            target,
            item.get("sha256") or "",
            opener=opener,
            expected_md5=item.get("md5") or "",
        )
        if _is_archive(target):
            extract(target, folder / "extracted")
        written.append(target)
    return written


__all__ = ["DatasetRefused", "ResearchDisabled", "planned_files", "run"]
