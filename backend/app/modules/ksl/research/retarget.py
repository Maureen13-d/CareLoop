"""Map landmark positions onto the stylized rig.

Arms use a simple direction from shoulder to elbow to wrist. Hands follow
the 21 MediaPipe bones and the bend is clamped. A missing channel holds
the last good pose instead of snapping back to neutral.
"""

from __future__ import annotations

import math

from app.modules.ksl.kmp import FACE_SHAPES, HAND_JOINTS

IDENTITY = [0.0, 0.0, 0.0, 1.0]
REST = (0.0, 1.0, 0.0)
MAX_HAND_BEND = math.radians(80)
# MediaPipe face mesh distances. These are coarse, not an expression model.
LEFT_EYE = (33, 263)
MOUTH = (13, 14)
LEFT_LID = (159, 145)
RIGHT_LID = (386, 374)
BROW = (70, 105)


def _dot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def _norm(vector: list[float] | tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(sum(value * value for value in vector)) or 1.0
    return (vector[0] / length, vector[1] / length, vector[2] / length)


def _quat_between(rest: tuple[float, float, float], direction: tuple[float, float, float]) -> list[float]:
    start, end = _norm(rest), _norm(direction)
    dot = max(-1.0, min(1.0, _dot(start, end)))
    if dot > 0.9999:
        return IDENTITY[:]
    if dot < -0.9999:
        return [1.0, 0.0, 0.0, 0.0]
    cross = _cross(start, end)
    quat = [cross[0], cross[1], cross[2], 1.0 + dot]
    length = math.sqrt(sum(value * value for value in quat)) or 1.0
    return [value / length for value in quat]


def _clamp_bend(quat: list[float], limit: float) -> list[float]:
    angle = 2 * math.acos(max(-1.0, min(1.0, quat[3])))
    if angle <= limit or angle < 1e-6:
        return quat
    half = angle / 2
    sine = math.sin(half) or 1.0
    axis = [quat[index] / sine for index in range(3)]
    new_half = limit / 2
    new_sine = math.sin(new_half)
    return [axis[0] * new_sine, axis[1] * new_sine, axis[2] * new_sine, math.cos(new_half)]


def _direction(start: list[float], end: list[float]) -> tuple[float, float, float]:
    return _norm((end[0] - start[0], end[1] - start[1], end[2] - start[2]))


def _hand(points: list[list[float]]) -> dict[str, list[float]] | None:
    if len(points) != 21:
        return None
    bones = {
        "wrist": (0, 9),
        "thumb_cmc": (1, 2),
        "thumb_mcp": (2, 3),
        "thumb_ip": (3, 4),
        "thumb_tip": (3, 4),
        "index_mcp": (5, 6),
        "index_pip": (6, 7),
        "index_dip": (7, 8),
        "index_tip": (7, 8),
        "middle_mcp": (9, 10),
        "middle_pip": (10, 11),
        "middle_dip": (11, 12),
        "middle_tip": (11, 12),
        "ring_mcp": (13, 14),
        "ring_pip": (14, 15),
        "ring_dip": (15, 16),
        "ring_tip": (15, 16),
        "pinky_mcp": (17, 18),
        "pinky_pip": (18, 19),
        "pinky_dip": (19, 20),
        "pinky_tip": (19, 20),
    }
    posed = {}
    for name in HAND_JOINTS:
        begin, finish = bones[name]
        posed[name] = _clamp_bend(_quat_between(REST, _direction(points[begin], points[finish])), MAX_HAND_BEND)
    return posed


def _arm(pose: list[list[float]], shoulder: int, elbow: int, wrist: int) -> dict[str, list[float]] | None:
    if len(pose) < 17:
        return None
    upper = _quat_between(REST, _direction(pose[shoulder], pose[elbow]))
    lower = _quat_between(REST, _direction(pose[elbow], pose[wrist]))
    return {"upper": upper, "lower": lower, "wrist": lower}


def _face(points: list[list[float]]) -> dict[str, float] | None:
    if len(points) < 468:
        return None
    eye = _dist(points[LEFT_EYE[0]], points[LEFT_EYE[1]]) or 1.0
    mouth = _dist(points[MOUTH[0]], points[MOUTH[1]]) / eye
    left_lid = _dist(points[LEFT_LID[0]], points[LEFT_LID[1]]) / eye
    right_lid = _dist(points[RIGHT_LID[0]], points[RIGHT_LID[1]]) / eye
    brow = _dist(points[BROW[0]], points[BROW[1]]) / eye
    weights = {name: 0.0 for name in FACE_SHAPES}
    weights["jawOpen"] = max(0.0, min(1.0, mouth * 4))
    weights["eyeBlinkLeft"] = max(0.0, min(1.0, 1 - left_lid * 8))
    weights["eyeBlinkRight"] = max(0.0, min(1.0, 1 - right_lid * 8))
    weights["browInnerUp"] = max(0.0, min(1.0, brow))
    return weights


def _dist(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))


def _hold(current: dict | None, previous: dict | None) -> dict:
    if current is not None:
        return current
    if previous is not None:
        return previous
    return {}


def retarget_clip(frames: list[dict]) -> list[dict]:
    posed: list[dict] = []
    last_arms = {"left": None, "right": None}
    last_hands = {"left": None, "right": None}
    last_face = None
    for frame in frames:
        pose = frame.get("pose") or []
        left_arm = _arm(pose, 11, 13, 15)
        right_arm = _arm(pose, 12, 14, 16)
        left_hand = _hand(frame.get("left_hand") or [])
        right_hand = _hand(frame.get("right_hand") or [])
        face = _face(frame.get("face") or [])
        left_arm = _hold(left_arm, last_arms["left"])
        right_arm = _hold(right_arm, last_arms["right"])
        left_hand = _hold(left_hand, last_hands["left"])
        right_hand = _hold(right_hand, last_hands["right"])
        face = _hold(face, last_face)
        if left_arm:
            last_arms["left"] = left_arm
        if right_arm:
            last_arms["right"] = right_arm
        if left_hand:
            last_hands["left"] = left_hand
        if right_hand:
            last_hands["right"] = right_hand
        if face:
            last_face = face
        posed.append(
            {
                "arms": {"left": left_arm, "right": right_arm},
                "hands": {"left": left_hand, "right": right_hand},
                "face": face,
            }
        )
    return posed
