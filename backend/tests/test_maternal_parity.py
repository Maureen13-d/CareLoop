"""The hub page and the server must agree on the shared fixture."""

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

from app.core.config import REPO_ROOT
from app.modules.maternal.devices import checksum
from app.modules.maternal.triage import triage_maternal

FIXTURE = REPO_ROOT / "rules" / "parity_fixture.json"
RUNNER = REPO_ROOT / "frontend" / "src" / "lib" / "parity-run.mjs"


def _aware(value):
    if isinstance(value, str) and value.endswith("Z"):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value


def _python(item):
    reading = {key: _aware(value) for key, value in item["reading"].items()}
    context = {key: _aware(value) for key, value in item.get("context", {}).items()}
    return triage_maternal(reading, item.get("signs") or [], context)


def _node(item):
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    completed = subprocess.run(
        [node, str(RUNNER)],
        input=json.dumps(item),
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def test_javascript_matches_the_server_on_the_shared_fixture():
    rows = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert len(rows) >= 12
    for item in rows:
        server = _python(item)
        browser = _node(item)
        assert browser["level"] == server["level"] == item["level"], item["name"]
        assert browser["rule_ids"] == server["rule_ids"], item["name"]


def test_sms_checksum_matches():
    body = "R|HUB-0007|1|120|80|70|0|"
    node = _node({"checksum_of": body})
    assert node["checksum"] == checksum(body)
