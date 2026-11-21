"""The dataset importer stays off until a person verifies the Zenodo licence."""

from __future__ import annotations

import hashlib
import io
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
import yaml

from app.modules.ksl.research.fetch import DatasetRefused, download, run
from app.modules.ksl.research.policy import ResearchDisabled, license_verified

ROOT = Path(__file__).resolve().parents[2]
# main.py mounts the dev research router. Patient, Telegram, and clip routes do not.
PATIENT_FILES = [
    "backend/app/modules/ksl/router.py",
    "backend/app/modules/ksl/registry.py",
    "backend/app/modules/ksl/manifest.py",
    "backend/app/modules/ksl/fallback.py",
    "backend/app/modules/ksl/guided.py",
    "backend/app/modules/ksl/review.py",
    "backend/app/modules/followup/telegram.py",
    "backend/app/modules/followup/conversation.py",
    "frontend/src/app/enter/EnterFlow.tsx",
    "frontend/src/ksl/SigningAvatar.tsx",
    "frontend/src/ksl/engine.js",
    "frontend/src/app/(app)/ksl/page.tsx",
]
NEEDLES = ("ksl.research", "ResearchAttribution", "researchLabel")


class _Body:
    def __init__(self, data: bytes):
        self._data = data
        self._pos = 0

    def read(self, size: int) -> bytes:
        chunk = self._data[self._pos : self._pos + size]
        self._pos += size
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _Headers:
    def __init__(self, values: dict[str, str]):
        self._values = values

    def get(self, key: str):
        return self._values.get(key)


class _Response(_Body):
    def __init__(self, data: bytes, headers: dict[str, str]):
        super().__init__(data)
        self.headers = _Headers(headers)


def _write_config(
    root: Path,
    verified: bool | str,
    digest: str = "",
    url: str = "",
    md5: str = "",
) -> None:
    folder = root / "config"
    folder.mkdir(parents=True, exist_ok=True)
    payload = {
        "ksl_dataset": {
            "license_verified": verified,
            "download_url": url,
            "sha256": digest,
            "md5": md5,
            "files": [],
        }
    }
    (folder / "ksl_dataset.yaml").write_text(yaml.safe_dump(payload), encoding="utf-8")


def _zip() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("clip/word.txt", b"pose")
    return buffer.getvalue()


def test_repo_config_records_the_owners_licence_check():
    assert license_verified(ROOT / "config" / "ksl_dataset.yaml") is True


def test_a_string_true_does_not_open_the_gate(tmp_path: Path):
    _write_config(tmp_path, "true")
    assert license_verified(tmp_path / "config" / "ksl_dataset.yaml") is False


def test_importer_does_not_download_while_the_licence_is_unverified(tmp_path: Path):
    _write_config(tmp_path, False)

    def opener(_url: str):
        raise AssertionError("network")

    with pytest.raises(ResearchDisabled):
        run(
            tmp_path,
            {"KSL_DATASET_URL": "https://example.invalid/data.zip", "KSL_DATASET_SHA256": "ab" * 32},
            opener=opener,
        )


def test_script_does_not_download_unless_asked():
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "fetch_ksl_dataset.py")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "Licence flag is on" in completed.stdout
    assert completed.stderr == ""


def test_verified_download_checks_the_hash_and_extracts(tmp_path: Path):
    payload = _zip()
    digest = hashlib.sha256(payload).hexdigest()
    _write_config(tmp_path, True, digest, "https://example.invalid/ksl_pose.zip")
    written = run(tmp_path, {}, opener=lambda _url: _Body(payload))
    assert written[0].is_file()
    extracted = tmp_path / "data" / "external" / "ksl_pose" / "extracted" / "clip" / "word.txt"
    assert extracted.read_bytes() == b"pose"
    assert not written[0].with_name(written[0].name + ".partial").exists()


def test_a_bad_checksum_keeps_nothing(tmp_path: Path):
    _write_config(tmp_path, True, "ab" * 32, "https://example.invalid/ksl_pose.zip")
    with pytest.raises(DatasetRefused):
        run(tmp_path, {}, opener=lambda _url: _Body(_zip()))
    folder = tmp_path / "data" / "external" / "ksl_pose"
    assert list(folder.glob("*")) == []


def test_archive_members_cannot_escape_the_dataset_folder(tmp_path: Path):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("../outside.txt", b"no")
    payload = buffer.getvalue()
    _write_config(tmp_path, True, hashlib.sha256(payload).hexdigest(), "https://example.invalid/ksl_pose.zip")
    with pytest.raises(DatasetRefused):
        run(tmp_path, {}, opener=lambda _url: _Body(payload))
    assert not (tmp_path / "outside.txt").exists()
    assert not (tmp_path.parent / "outside.txt").exists()


def test_md5_from_the_record_is_enough(tmp_path: Path):
    payload = _zip()
    digest = hashlib.md5(payload).hexdigest()
    _write_config(tmp_path, True, "", "https://example.invalid/ksl_pose.zip", md5=digest)
    written = run(tmp_path, {}, opener=lambda _url: _Body(payload))
    assert written[0].is_file()


def test_download_stops_before_filling_the_disk(tmp_path: Path):
    body = _Response(b"zip", {"Content-Length": "999999"})
    with pytest.raises(DatasetRefused, match="disk"):
        download(
            "https://example.invalid/ksl_pose.zip",
            tmp_path / "ksl_pose.zip",
            expected_md5="ab" * 16,
            opener=lambda _url: body,
            free_bytes=10,
        )
    assert list(tmp_path.iterdir()) == []


def test_patient_paths_do_not_import_the_research_module():
    for relative in PATIENT_FILES:
        text = (ROOT / relative).read_text(encoding="utf-8")
        for needle in NEEDLES:
            assert needle not in text, relative
