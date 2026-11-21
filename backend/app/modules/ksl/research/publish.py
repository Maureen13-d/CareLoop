"""A research packet the dev page can draw. Dataset files stay out of this."""

from __future__ import annotations

from typing import Any

PLAYBACK_FPS = 12
FACE_KEYS = ("jawOpen", "eyeBlinkLeft", "eyeBlinkRight", "browInnerUp")


def _xy(points: list[list[float]] | None) -> list[list[float]]:
    return [[float(point[0]), float(point[1])] for point in (points or [])]


def public_clip(packet: dict[str, Any], posed: list[dict]) -> dict[str, Any]:
    frames = []
    for frame, rig in zip(packet["frames"], posed, strict=True):
        face = rig.get("face") or {}
        frames.append(
            {
                "pose": _xy(frame.get("pose")),
                "left_hand": _xy(frame.get("left_hand")),
                "right_hand": _xy(frame.get("right_hand")),
                "arms": rig.get("arms") or {},
                "hands": rig.get("hands") or {},
                "face": {name: float(face.get(name, 0.0)) for name in FACE_KEYS},
            }
        )
    return {
        "kind": "research-motion-1",
        "word_label": packet["word_label"],
        "source_id": packet["source_id"],
        "fps": None,
        "playback_fps": PLAYBACK_FPS,
        "quality": packet["quality"],
        "frames": frames,
    }
