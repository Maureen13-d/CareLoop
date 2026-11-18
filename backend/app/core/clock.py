"""Demo clock.

All business logic asks this module for "now" so a demo can move time forward
(for example 3 days) and show an escalation in seconds. The offset lives in
memory and resets when the server restarts. Times are naive UTC.
"""
from datetime import UTC, datetime, timedelta

_offset = timedelta(0)


def now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None) + _offset


def advance(hours: float) -> datetime:
    global _offset
    _offset += timedelta(hours=hours)
    return now()


def reset() -> None:
    global _offset
    _offset = timedelta(0)


def offset_hours() -> float:
    return _offset.total_seconds() / 3600
