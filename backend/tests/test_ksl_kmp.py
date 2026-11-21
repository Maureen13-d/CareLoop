"""Validator tests for the motion packet. The clip is not a sign."""

import json
from pathlib import Path

from app.modules.ksl.kmp import (
    FACE_SHAPES,
    HAND_JOINTS,
    TEST_LABEL,
    build_test_clip,
    decompress,
    encoded_size,
    validate,
)

ROOT = Path(__file__).resolve().parents[2]
CLIP = ROOT / "assets" / "ksl" / "placeholders" / "test_motion.json"


def test_rig_counts():
    assert len(HAND_JOINTS) == 21
    assert len(FACE_SHAPES) == 52


def test_wave_clip_is_labelled_and_small():
    packet = build_test_clip()
    assert packet["label"] == TEST_LABEL
    assert validate(packet) == []
    assert encoded_size(packet) < 150_000
    frames = decompress(packet)["frames"]
    assert frames["face"][11]["eyeBlinkLeft"] == 1
    assert frames["body"][8]["upper_arm_r"] != [0.0, 0.0, 0.0, 1.0]


def test_checked_in_placeholder_matches_the_builder():
    packet = json.loads(CLIP.read_text(encoding="utf-8"))
    assert packet["label"] == TEST_LABEL
    assert validate(packet) == []
    assert encoded_size(packet) < 150_000


def test_a_short_payload_is_rejected():
    packet = build_test_clip(frames=2)
    packet["payload_b64"] = "AAAA"
    assert validate(packet)
