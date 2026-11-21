"""Public patient IDs. Random, grouped, with a check digit. Not sequential."""

import secrets

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _check(body: str) -> str:
    total = sum(index * ALPHABET.index(char) for index, char in enumerate(body, start=1))
    return ALPHABET[total % len(ALPHABET)]


def new_public_id() -> str:
    body = "".join(secrets.choice(ALPHABET) for _ in range(12))
    raw = body + _check(body)
    return _grouped(raw)


def parse_public_id(value: str) -> str | None:
    """Return the canonical ID, or None when the check digit or shape is wrong."""
    raw = "".join(char for char in (value or "").upper() if char in ALPHABET)
    if len(raw) != 13 or _check(raw[:12]) != raw[12]:
        return None
    return _grouped(raw)


def _grouped(raw: str) -> str:
    return f"{raw[0:4]}-{raw[4:8]}-{raw[8:12]}-{raw[12]}"
