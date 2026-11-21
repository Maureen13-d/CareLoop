"""How2Sign clips stay off production and off the patient clip route."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.asl.router import ASL_LABEL, router

ROOT = Path(__file__).resolve().parents[2]


def test_production_hides_asl(monkeypatch):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    client = TestClient(app)
    monkeypatch.setenv("CARELOOP_ENV", "production")
    assert client.get("/api/v1/dev/asl-research/clips").status_code == 404


def test_only_the_two_sentences_are_served(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("CARELOOP_ENV", "demo")
    monkeypatch.setenv("ASL_RESEARCH_PACKETS", str(tmp_path))
    (tmp_path / "manifest.json").write_text(
        json.dumps([{"id": "HI", "sentence": "Hi!"}]),
        encoding="utf-8",
    )
    (tmp_path / "HI.json").write_text(json.dumps({"sentence": "Hi!", "frames": []}), encoding="utf-8")
    (tmp_path / "OTHER.json").write_text("{}", encoding="utf-8")
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    client = TestClient(app)
    listed = client.get("/api/v1/dev/asl-research/clips")
    assert listed.status_code == 200
    assert listed.json()["clips"] == [{"id": "HI", "sentence": "Hi!"}]
    assert listed.json()["label"] == ASL_LABEL
    body = client.get("/api/v1/dev/asl-research/clips/HI")
    assert body.json()["label"] == ASL_LABEL
    assert client.get("/api/v1/dev/asl-research/clips/OTHER").status_code == 404


def test_patient_clip_registry_does_not_import_asl():
    text = (ROOT / "backend/app/modules/ksl/registry.py").read_text(encoding="utf-8")
    assert "modules.asl" not in text
    assert "How2Sign" not in text
