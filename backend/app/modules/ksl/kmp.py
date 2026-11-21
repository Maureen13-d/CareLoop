"""KSL Motion Packet. Recorded motion only. This module does not invent signs."""

from __future__ import annotations

import base64
import hashlib
import json
import math
import struct
from typing import Any

FPS = 30
QUAT_SCALE = 32767
WEIGHT_SCALE = 127

BODY_JOINTS = (
    "hips",
    "spine",
    "spine2",
    "chest",
    "neck",
    "head",
    "shoulder_l",
    "shoulder_r",
    "upper_arm_l",
    "upper_arm_r",
    "lower_arm_l",
    "lower_arm_r",
    "wrist_l",
    "wrist_r",
)
HAND_JOINTS = (
    "wrist",
    "thumb_cmc",
    "thumb_mcp",
    "thumb_ip",
    "thumb_tip",
    "index_mcp",
    "index_pip",
    "index_dip",
    "index_tip",
    "middle_mcp",
    "middle_pip",
    "middle_dip",
    "middle_tip",
    "ring_mcp",
    "ring_pip",
    "ring_dip",
    "ring_tip",
    "pinky_mcp",
    "pinky_pip",
    "pinky_dip",
    "pinky_tip",
)
FACE_SHAPES = (
    "browDownLeft",
    "browDownRight",
    "browInnerUp",
    "browOuterUpLeft",
    "browOuterUpRight",
    "cheekPuff",
    "cheekSquintLeft",
    "cheekSquintRight",
    "eyeBlinkLeft",
    "eyeBlinkRight",
    "eyeLookDownLeft",
    "eyeLookDownRight",
    "eyeLookInLeft",
    "eyeLookInRight",
    "eyeLookOutLeft",
    "eyeLookOutRight",
    "eyeLookUpLeft",
    "eyeLookUpRight",
    "eyeSquintLeft",
    "eyeSquintRight",
    "eyeWideLeft",
    "eyeWideRight",
    "jawForward",
    "jawLeft",
    "jawOpen",
    "jawRight",
    "mouthClose",
    "mouthDimpleLeft",
    "mouthDimpleRight",
    "mouthFrownLeft",
    "mouthFrownRight",
    "mouthFunnel",
    "mouthLeft",
    "mouthLowerDownLeft",
    "mouthLowerDownRight",
    "mouthPressLeft",
    "mouthPressRight",
    "mouthPucker",
    "mouthRight",
    "mouthRollLower",
    "mouthRollUpper",
    "mouthShrugLower",
    "mouthShrugUpper",
    "mouthSmileLeft",
    "mouthSmileRight",
    "mouthStretchLeft",
    "mouthStretchRight",
    "mouthUpperUpLeft",
    "mouthUpperUpRight",
    "noseSneerLeft",
    "noseSneerRight",
    "tongueOut",
)
TEST_LABEL = "TEST_MOTION_NOT_SIGN"
PLACEHOLDER_LABEL = "PLACEHOLDER MOTION: NOT KSL"
BLOCKED_LABELS = {TEST_LABEL, PLACEHOLDER_LABEL}


def source_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _ident() -> list[float]:
    return [0.0, 0.0, 0.0, 1.0]


def _clamp_quat(values: list[float]) -> list[int]:
    return [max(-QUAT_SCALE, min(QUAT_SCALE, round(v * QUAT_SCALE))) for v in values]


def _quat_from_z(degrees: float) -> list[float]:
    half = math.radians(degrees) / 2
    return [0.0, 0.0, math.sin(half), math.cos(half)]


def build_test_clip(frames: int = 90) -> dict[str, Any]:
    """A waving arm and a blink. Not a sign. Not KSL."""
    body = []
    hands_l = []
    hands_r = []
    face = []
    gaze = []
    head = []
    for index in range(frames):
        wave = math.sin(index / 8) * 35
        body.append({name: _ident() for name in BODY_JOINTS} | {"upper_arm_r": _quat_from_z(wave)})
        hands_l.append({name: _ident() for name in HAND_JOINTS})
        hands_r.append({name: _ident() for name in HAND_JOINTS})
        blink = 1.0 if 10 <= (index % 45) <= 13 else 0.0
        weights = {name: 0.0 for name in FACE_SHAPES}
        weights["eyeBlinkLeft"] = blink
        weights["eyeBlinkRight"] = blink
        face.append(weights)
        gaze.append({"left": [0.0, 0.0, 1.0], "right": [0.0, 0.0, 1.0]})
        head.append(_ident())
    packet = {
        "clip_id": "test-wave",
        "template_id": "test_motion",
        "source_text_hash": source_hash("TEST_MOTION_NOT_SIGN"),
        "signer_pseudonym": "synthetic",
        "capture_method": "procedural",
        "label": TEST_LABEL,
        "fps": FPS,
        "frame_count": frames,
        "duration_ms": int(frames / FPS * 1000),
        "rig_version": "kmp-1",
        "quality_score": 0,
        "frames": {
            "body": body,
            "hands": {"left": hands_l, "right": hands_r},
            "face": face,
            "gaze": gaze,
            "head": head,
        },
    }
    return compress(packet)


def compress(packet: dict[str, Any]) -> dict[str, Any]:
    frames = packet["frames"]
    blob = _pack_frames(frames)
    stored = {key: value for key, value in packet.items() if key != "frames"}
    stored["encoding"] = "delta-int16-v1"
    stored["payload_b64"] = base64.b64encode(blob).decode("ascii")
    return stored


def decompress(packet: dict[str, Any]) -> dict[str, Any]:
    if "frames" in packet:
        return packet
    raw = base64.b64decode(packet["payload_b64"])
    full = dict(packet)
    full["frames"] = _unpack_frames(raw, int(packet["frame_count"]))
    return full


def _pack_quat_map(frames: list[dict[str, list[float]]], names: tuple[str, ...]) -> bytes:
    previous = {name: [0, 0, 0, QUAT_SCALE] for name in names}
    chunks = []
    for frame in frames:
        for name in names:
            current = _clamp_quat(frame[name])
            delta = [current[i] - previous[name][i] for i in range(4)]
            chunks.append(struct.pack("<4h", *delta))
            previous[name] = current
    return b"".join(chunks)


def _pack_frames(frames: dict[str, Any]) -> bytes:
    count = len(frames["body"])
    parts = [struct.pack("<H", count)]
    parts.append(_pack_quat_map(frames["body"], BODY_JOINTS))
    parts.append(_pack_quat_map(frames["hands"]["left"], HAND_JOINTS))
    parts.append(_pack_quat_map(frames["hands"]["right"], HAND_JOINTS))
    parts.append(_pack_weights(frames["face"]))
    parts.append(_pack_gaze(frames["gaze"]))
    parts.append(_pack_quat_list(frames["head"]))
    return b"".join(parts)


def _pack_weights(frames: list[dict[str, float]]) -> bytes:
    previous = {name: 0 for name in FACE_SHAPES}
    chunks = []
    for frame in frames:
        for name in FACE_SHAPES:
            current = max(0, min(WEIGHT_SCALE, round(frame[name] * WEIGHT_SCALE)))
            delta = max(-128, min(127, current - previous[name]))
            chunks.append(struct.pack("<b", delta))
            previous[name] = current
    return b"".join(chunks)


def _pack_gaze(frames: list[dict[str, list[float]]]) -> bytes:
    chunks = []
    for frame in frames:
        for side in ("left", "right"):
            chunks.append(struct.pack("<3h", *_clamp_quat(frame[side][:3])))
    return b"".join(chunks)


def _pack_quat_list(frames: list[list[float]]) -> bytes:
    previous = [0, 0, 0, QUAT_SCALE]
    chunks = []
    for frame in frames:
        current = _clamp_quat(frame)
        delta = [current[i] - previous[i] for i in range(4)]
        chunks.append(struct.pack("<4h", *delta))
        previous = current
    return b"".join(chunks)


def _unpack_frames(raw: bytes, count: int) -> dict[str, Any]:
    view = memoryview(raw)
    offset = 2
    body, offset = _unpack_quat_map(view, offset, count, BODY_JOINTS)
    left, offset = _unpack_quat_map(view, offset, count, HAND_JOINTS)
    right, offset = _unpack_quat_map(view, offset, count, HAND_JOINTS)
    face, offset = _unpack_weights(view, offset, count)
    gaze, offset = _unpack_gaze(view, offset, count)
    head, offset = _unpack_quat_list(view, offset, count)
    if offset != len(raw):
        raise ValueError("motion packet has trailing bytes")
    return {"body": body, "hands": {"left": left, "right": right}, "face": face, "gaze": gaze, "head": head}


def _unpack_quat_map(view, offset, count, names):
    previous = {name: [0, 0, 0, QUAT_SCALE] for name in names}
    frames = []
    for _ in range(count):
        frame = {}
        for name in names:
            delta = struct.unpack_from("<4h", view, offset)
            offset += 8
            current = [previous[name][i] + delta[i] for i in range(4)]
            previous[name] = current
            frame[name] = [value / QUAT_SCALE for value in current]
        frames.append(frame)
    return frames, offset


def _unpack_weights(view, offset, count):
    previous = {name: 0 for name in FACE_SHAPES}
    frames = []
    for _ in range(count):
        frame = {}
        for name in FACE_SHAPES:
            delta = struct.unpack_from("<b", view, offset)[0]
            offset += 1
            current = max(0, min(WEIGHT_SCALE, previous[name] + delta))
            previous[name] = current
            frame[name] = current / WEIGHT_SCALE
        frames.append(frame)
    return frames, offset


def _unpack_gaze(view, offset, count):
    frames = []
    for _ in range(count):
        frame = {}
        for side in ("left", "right"):
            raw = struct.unpack_from("<3h", view, offset)
            offset += 6
            frame[side] = [value / QUAT_SCALE for value in raw]
        frames.append(frame)
    return frames, offset


def _unpack_quat_list(view, offset, count):
    previous = [0, 0, 0, QUAT_SCALE]
    frames = []
    for _ in range(count):
        delta = struct.unpack_from("<4h", view, offset)
        offset += 8
        current = [previous[i] + delta[i] for i in range(4)]
        previous = current
        frames.append([value / QUAT_SCALE for value in current])
    return frames, offset


def validate(packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in (
        "clip_id",
        "template_id",
        "source_text_hash",
        "signer_pseudonym",
        "capture_method",
        "label",
        "fps",
        "frame_count",
        "duration_ms",
        "rig_version",
    ):
        if key not in packet:
            errors.append(f"missing {key}")
    if packet.get("fps") != FPS:
        errors.append("fps must be 30")
    try:
        frames = decompress(packet)["frames"]
    except (KeyError, ValueError, struct.error) as exc:
        return errors + [f"payload: {exc}"]
    count = int(packet.get("frame_count") or 0)
    if len(frames["body"]) != count:
        errors.append("frame count does not match body")
    if count and set(frames["body"][0]) != set(BODY_JOINTS):
        errors.append("body joints do not match the rig")
    if count and set(frames["hands"]["left"][0]) != set(HAND_JOINTS):
        errors.append("left hand joints do not match the rig")
    if count and set(frames["face"][0]) != set(FACE_SHAPES):
        errors.append("face shapes do not match the rig")
    if count and "head" not in frames:
        errors.append("head pose channel is missing")
    return errors


def encoded_size(packet: dict[str, Any]) -> int:
    return len(json.dumps(packet, separators=(",", ":")).encode("utf-8"))


def blocked_in_production(packet: dict[str, Any], production: bool) -> bool:
    return production and packet.get("label") in BLOCKED_LABELS
