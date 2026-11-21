"""Telegram webhook and simulator. Rules stay in the conversation core."""

import hmac
import os

from sqlalchemy.orm import Session

from app.core import clock
from app.core.errors import DomainError
from app.modules.followup.conversation import get_session, handle, log_outbound


def signature_ok(header: str | None) -> bool:
    secret = os.environ.get("CARELOOP_TELEGRAM_WEBHOOK_SECRET", "")
    if not secret or not header:
        return False
    return hmac.compare_digest(header, secret)


def ingest(db: Session, *, chat_id: str, text: str, update_id: str | None) -> dict:
    session = get_session(db, "telegram", str(chat_id))
    if update_id and session.last_update_id == update_id:
        return {"duplicate": True, "reply_text": "", "escalation_label": None}
    result = handle(db, session, text)
    session.last_update_id = update_id
    session.updated_at = clock.now()
    # The person just wrote, so this reply is inside the window they opened.
    log_outbound(
        db,
        session.public_id,
        "telegram",
        "reply",
        "freeform",
        result["reply_text"],
    )
    db.commit()
    result["mode_label"] = "freeform"
    result["synthetic"] = True
    return result


def require_signature(header: str | None) -> None:
    if not signature_ok(header):
        raise DomainError(401, "bad_signature", "Signature was not accepted")
