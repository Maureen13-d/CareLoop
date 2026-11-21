"""ID plus a one-time code. Unknown and wrong IDs look the same."""

import hashlib
import hmac
import os
import secrets
from datetime import UTC, timedelta

import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.config import settings
from app.core.security import ALGORITHM
from app.modules.followup.models import AccessCode

REJECTED = "That ID or code was not accepted."
_LIMIT = 5
_LOCK_MINUTES = 15
_CODE_MINUTES = 5
_SESSION_MINUTES = 15
_fails: dict[tuple[str, str], dict] = {}
_dev_codes: dict[str, str] = {}


def reset_limits() -> None:
    _fails.clear()
    _dev_codes.clear()


def expose_codes() -> bool:
    flag = os.environ.get("CARELOOP_EXPOSE_SIMULATED_CODES", "true")
    return flag.lower() not in {"0", "false", "no"}


def _bucket(kind: str, key: str) -> dict:
    return _fails.setdefault((kind, key), {"fails": 0, "until": None})


def locked(kind: str, key: str, now) -> bool:
    until = _bucket(kind, key)["until"]
    return until is not None and until > now


def _fail(kind: str, key: str, now) -> None:
    row = _bucket(kind, key)
    row["fails"] += 1
    if row["fails"] >= _LIMIT:
        row["until"] = now + timedelta(minutes=_LOCK_MINUTES)


def _clear(kind: str, key: str) -> None:
    _fails.pop((kind, key), None)


def _digest(code: str) -> str:
    return hmac.new(settings.secret_key.encode(), code.encode(), hashlib.sha256).hexdigest()


def issue_code(db: Session, public_id: str) -> None:
    code = f"{secrets.randbelow(1_000_000):06d}"
    now = clock.now()
    db.add(
        AccessCode(
            public_id=public_id,
            code_hash=_digest(code),
            expires_at=now + timedelta(minutes=_CODE_MINUTES),
        )
    )
    if expose_codes():
        _dev_codes[public_id] = code
    db.flush()


def dev_code(public_id: str) -> str | None:
    if not expose_codes():
        return None
    return _dev_codes.get(public_id)


def code_ok(db: Session, public_id: str, code: str, client_key: str) -> bool:
    now = clock.now()
    if locked("id", public_id, now) or locked("client", client_key or "none", now):
        return False
    digest = _digest(code or "")
    row = db.scalar(
        select(AccessCode)
        .where(
            AccessCode.public_id == public_id,
            AccessCode.used_at.is_(None),
            AccessCode.expires_at >= now,
        )
        .order_by(AccessCode.id.desc())
    )
    if row is None or not hmac.compare_digest(row.code_hash, digest):
        _fail("id", public_id, now)
        _fail("client", client_key or "none", now)
        return False
    row.used_at = now
    _clear("id", public_id)
    _clear("client", client_key or "none")
    db.flush()
    return True


def issue_token(public_id: str) -> str:
    exp = clock.now().replace(tzinfo=UTC) + timedelta(minutes=_SESSION_MINUTES)
    return jwt.encode(
        {"sub": f"followup:{public_id}", "role": "followup_patient", "exp": exp},
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def read_token(token: str | None) -> str | None:
    if not token:
        return None
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
            options={"verify_exp": False},
        )
    except jwt.PyJWTError:
        return None
    if payload.get("role") != "followup_patient":
        return None
    exp = payload.get("exp")
    exp_ts = exp if isinstance(exp, (int, float)) else None
    if exp_ts is None:
        return None
    if exp_ts < clock.now().replace(tzinfo=UTC).timestamp():
        return None
    sub = str(payload.get("sub", ""))
    if not sub.startswith("followup:"):
        return None
    return sub.split(":", 1)[1]
