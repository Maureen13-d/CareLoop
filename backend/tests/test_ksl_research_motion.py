"""Research clips stay synthetic in tests and off the patient routes."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.ksl.research.normalize import normalize_clip
from app.modules.ksl.research.overlay import BANNER, RESEARCH_LABEL, frame_svg, stamp_banner
from app.modules.ksl.research.retarget import retarget_clip
from app.modules.ksl.research.router import router

ROOT = Path(__file__).resolve().parents[2]


def _pose(wrist_drop: float = 1.0) -> list[list[float]]:
    points = [[0.0, 0.0, 0.0] for _ in range(33)]
    points[11] = [-0.5, 0.0, 0.0]
    points[12] = [0.5, 0.0, 0.0]
    points[13] = [-0.5, 0.5, 0.0]
    points[14] = [0.5, 0.5, 0.0]
    points[15] = [-0.5, wrist_drop, 0.0]
    points[16] = [0.5, wrist_drop, 0.0]
    return points


def _hand(spread: float = 0.1) -> list[list[float]]:
    points = [[0.0, 0.0, 0.0] for _ in range(21)]
    for index in range(1, 21):
        points[index] = [spread * (index % 5), 0.05 * index, 0.0]
    return points


def _face(mouth: float) -> list[list[float]]:
    points = [[0.0, 0.0, 0.0] for _ in range(468)]
    points[33] = [-0.2, 0.0, 0.0]
    points[263] = [0.2, 0.0, 0.0]
    points[13] = [0.0, 0.0, 0.0]
    points[14] = [0.0, mouth, 0.0]
    points[159] = [0.0, 0.0, 0.0]
    points[145] = [0.0, 0.05, 0.0]
    points[386] = [0.0, 0.0, 0.0]
    points[374] = [0.0, 0.05, 0.0]
    points[70] = [0.0, 0.0, 0.0]
    points[105] = [0.1, 0.0, 0.0]
    return points


def test_normalize_is_deterministic_and_centers_on_the_shoulders():
    frame = {"pose": _pose(), "left_hand": _hand(), "right_hand": _hand(), "face": []}
    first = normalize_clip([frame, frame], source_id="fixture", word_label="STOP")
    second = normalize_clip([frame, frame], source_id="fixture", word_label="STOP")
    assert first == second
    assert first is not None
    shoulder = first["frames"][0]["pose"][11]
    assert abs(shoulder[0] + 0.5) < 1e-6
    assert first["fps"] is None


def test_a_short_hand_gap_is_filled_and_a_dead_clip_is_dropped():
    present = {"pose": _pose(), "left_hand": _hand(), "right_hand": _hand(), "face": []}
    missing = {"pose": _pose(), "left_hand": [], "right_hand": _hand(), "face": []}
    filled = normalize_clip([present, missing, present], source_id="fixture", word_label="HELP")
    assert filled is not None
    assert len(filled["frames"][1]["left_hand"]) == 21
    empty = {"pose": _pose(), "left_hand": [], "right_hand": [], "face": []}
    assert normalize_clip([empty, empty], source_id="fixture", word_label="NO") is None


def test_a_missing_hand_holds_the_last_pose():
    pose = _pose()
    hand = _hand()
    frames = [
        {"pose": pose, "left_hand": hand, "right_hand": hand, "face": []},
        {"pose": pose, "left_hand": [], "right_hand": hand, "face": []},
        {"pose": pose, "left_hand": hand, "right_hand": hand, "face": []},
    ]
    posed = retarget_clip(frames)
    assert posed[1]["hands"]["left"] == posed[0]["hands"]["left"]
    assert posed[1]["hands"]["left"] != {}


def test_an_open_mouth_raises_the_jaw_weight():
    closed = retarget_clip([{"pose": _pose(), "left_hand": [], "right_hand": [], "face": _face(0.01)}])
    opened = retarget_clip([{"pose": _pose(), "left_hand": [], "right_hand": [], "face": _face(0.3)}])
    assert opened[0]["face"]["jawOpen"] > closed[0]["face"]["jawOpen"]


def test_the_banner_is_in_the_pixels_and_the_svg_text():
    pixels = stamp_banner()
    assert pixels[0] == BANNER
    assert all(pixel == BANNER for pixel in pixels)
    picture = frame_svg([(120.0, 80.0, 140.0, 160.0)])
    assert RESEARCH_LABEL in picture
    assert 'id="research-banner"' in picture
    label_js = (ROOT / "frontend/src/ksl/researchLabel.js").read_text(encoding="utf-8")
    assert RESEARCH_LABEL in label_js


def test_production_and_a_closed_licence_hide_the_route(monkeypatch):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    client = TestClient(app)
    monkeypatch.setenv("CARELOOP_ENV", "production")
    assert client.get("/api/v1/dev/ksl-research/words").status_code == 404
    monkeypatch.setenv("CARELOOP_ENV", "demo")
    monkeypatch.setattr("app.modules.ksl.research.router.license_verified", lambda path=None: False)
    assert client.get("/api/v1/dev/ksl-research/words").status_code == 404


def test_a_research_packet_is_served_only_from_the_shortlist(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("CARELOOP_ENV", "demo")
    monkeypatch.setenv("KSL_RESEARCH_PACKETS", str(tmp_path))
    (tmp_path / "PAIN.json").write_text(json.dumps({"word_label": "PAIN", "frames": []}), encoding="utf-8")
    (tmp_path / "CANCER.json").write_text("{}", encoding="utf-8")
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    client = TestClient(app)
    listed = client.get("/api/v1/dev/ksl-research/words")
    assert listed.status_code == 200
    assert listed.json()["words"] == ["PAIN"]
    assert RESEARCH_LABEL in listed.json()["label"]
    body = client.get("/api/v1/dev/ksl-research/words/PAIN")
    assert body.status_code == 200
    assert body.json()["label"] == RESEARCH_LABEL
    assert client.get("/api/v1/dev/ksl-research/words/CANCER").status_code == 404


def test_the_app_does_not_load_pickles_or_a_research_recognizer():
    for path in (ROOT / "backend" / "app").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "allow_pickle" not in text
        assert "research.recognizer" not in text
    assert list((ROOT / "backend" / "app").rglob("*recognizer*")) == []


def test_patient_templates_do_not_name_a_research_clip():
    for path in (ROOT / "config").rglob("*.yaml"):
        text = path.read_text(encoding="utf-8")
        assert "research-motion" not in text
        assert "RESEARCH SAMPLE" not in text
    registry = (ROOT / "backend/app/modules/ksl/registry.py").read_text(encoding="utf-8")
    assert "ksl.research" not in registry
