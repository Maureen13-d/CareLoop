"""Turn plain landmark frames into a centered, scored research clip.

This module does not read dataset files and does not unpickle anything.
Left and right stay as the source named them. Pose index 11 is the
subject's left shoulder, index 12 the right, in MediaPipe order.
"""

from __future__ import annotations

import math
from typing import Any

Point = list[float]
Frame = dict[str, list[Point]]

EXPECTED = {"pose": 33, "left_hand": 21, "right_hand": 21, "face": 468}
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_WRIST = 15
RIGHT_WRIST = 16

DEFAULTS = {
    "max_gap": 2,
    "smooth_pose": 0.45,
    "smooth_hands": 0.9,
    "smooth_face": 0.5,
    "idle_motion": 0.03,
    "drop_missing_hands": 0.8,
}


def _dist(a: Point, b: Point) -> float:
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def _valid(points: list[Point], count: int) -> bool:
    return len(points) == count


def _center_frame(frame: Frame, expected: dict[str, int]) -> tuple[Frame, float]:
    pose = frame.get("pose") or []
    if not _valid(pose, expected["pose"]):
        return {key: [] for key in expected}, 0.0
    left, right = pose[LEFT_SHOULDER], pose[RIGHT_SHOULDER]
    width = _dist(left, right)
    if width < 1e-6:
        return {key: [] for key in expected}, 0.0
    mid = [(left[i] + right[i]) / 2 for i in range(3)]

    def shift(points: list[Point], count: int) -> list[Point]:
        if not _valid(points, count):
            return []
        return [[(point[i] - mid[i]) / width for i in range(3)] for point in points]

    return {key: shift(frame.get(key) or [], count) for key, count in expected.items()}, 1.0


def _fill_gaps(series: list[list[Point]], limit: int) -> list[list[Point]]:
    filled = [list(points) for points in series]
    index = 0
    while index < len(filled):
        if filled[index]:
            index += 1
            continue
        end = index
        while end < len(filled) and not filled[end]:
            end += 1
        gap = end - index
        if 0 < gap <= limit and index > 0 and end < len(filled):
            before, after = filled[index - 1], filled[end]
            if len(before) == len(after) and before:
                for step in range(gap):
                    weight = (step + 1) / (gap + 1)
                    filled[index + step] = [
                        [
                            before[point][axis] * (1 - weight) + after[point][axis] * weight
                            for axis in range(3)
                        ]
                        for point in range(len(before))
                    ]
        index = end + 1
    return filled


def _smooth(series: list[list[Point]], alpha: float) -> list[list[Point]]:
    previous: list[Point] | None = None
    smoothed: list[list[Point]] = []
    for points in series:
        if not points or previous is None or len(previous) != len(points):
            smoothed.append(points)
            if points:
                previous = points
            continue
        blended = [
            [
                previous[point][axis] * (1 - alpha) + points[point][axis] * alpha
                for axis in range(3)
            ]
            for point in range(len(points))
        ]
        smoothed.append(blended)
        previous = blended
    return smoothed


def _wrists(frame: Frame) -> tuple[Point, Point] | None:
    pose = frame.get("pose") or []
    if len(pose) <= RIGHT_WRIST:
        return None
    return pose[LEFT_WRIST], pose[RIGHT_WRIST]


def _trim_idle(frames: list[Frame], threshold: float) -> list[Frame]:
    if len(frames) < 3:
        return frames

    def moving(earlier: Frame, later: Frame) -> bool:
        left, right = _wrists(earlier), _wrists(later)
        if left is None or right is None:
            return True
        motion = _dist(left[0], right[0]) + _dist(left[1], right[1])
        return motion >= threshold

    start = 0
    while start < len(frames) - 2 and not moving(frames[start], frames[start + 1]):
        start += 1
    end = len(frames)
    while end - start > 2 and not moving(frames[end - 2], frames[end - 1]):
        end -= 1
    return frames[start:end]


def _quality(frames: list[Frame]) -> float:
    if not frames:
        return 0.0
    hands = 0
    motion = 0.0
    previous = None
    for frame in frames:
        left = bool(frame.get("left_hand"))
        right = bool(frame.get("right_hand"))
        if left or right:
            hands += 1
        wrists = _wrists(frame)
        if previous and wrists:
            motion += min(1.0, _dist(previous[0], wrists[0]) + _dist(previous[1], wrists[1]))
        if wrists:
            previous = wrists
    coverage = hands / len(frames)
    activity = motion / len(frames)
    return round(0.7 * coverage + 0.3 * min(1.0, activity), 4)


def normalize_clip(
    frames: list[Frame],
    *,
    source_id: str,
    word_label: str,
    settings: dict[str, Any] | None = None,
    expected: dict[str, int] | None = None,
) -> dict[str, Any] | None:
    """Return a research packet, or None when too many hands are missing."""
    options = {**DEFAULTS, **(settings or {})}
    counts = {**EXPECTED, **(expected or {})}
    centered: list[Frame] = []
    for frame in frames:
        cleaned, confidence = _center_frame(frame, counts)
        if confidence:
            centered.append(cleaned)
    if not centered:
        return None
    channels = {}
    for name, alpha_key in (
        ("pose", "smooth_pose"),
        ("left_hand", "smooth_hands"),
        ("right_hand", "smooth_hands"),
        ("face", "smooth_face"),
    ):
        series = [frame[name] for frame in centered]
        series = _fill_gaps(series, int(options["max_gap"]))
        channels[name] = _smooth(series, float(options[alpha_key]))
    packed = [
        {name: channels[name][index] for name in channels}
        for index in range(len(centered))
    ]
    packed = _trim_idle(packed, float(options["idle_motion"]))
    missing_both = 0
    for frame in packed:
        if not frame.get("left_hand") and not frame.get("right_hand"):
            missing_both += 1
    if packed and missing_both / len(packed) > float(options["drop_missing_hands"]):
        return None
    return {
        "kind": "research-motion-1",
        "source_id": source_id,
        "word_label": word_label,
        "fps": None,
        "frames": packed,
        "quality": _quality(packed),
    }
