"""Shared API types."""

from datetime import datetime
from typing import Annotated

from pydantic import PlainSerializer

# Stored as naive UTC; always sent to clients as ISO 8601 with a trailing Z.
UtcDatetime = Annotated[
    datetime,
    PlainSerializer(
        lambda d: d.isoformat(timespec="seconds") + "Z" if d else None, return_type=str | None
    ),
]
