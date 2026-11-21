"""Telegram webhook, outbound send, and the staff simulator."""

import hmac
import time

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.errors import DomainError
from app.modules.followup.conversation import get_session, log_outbound
from app.modules.followup.telegram_env import present
from app.modules.followup.telegram_flow import (
    checkin_messages,
    link_url,
    mark_unreachable,
    mint_link,
    session_key,
    turn,
)
from app.modules.followup.telegram_models import TelegramVault
from app.modules.ksl.registry import for_channel

API = "https://api.telegram.org"


def signature_ok(header: str | None) -> bool:
    secret = present("webhook_secret")
    if not secret or not header:
        return False
    return hmac.compare_digest(header, secret)


def require_signature(header: str | None) -> None:
    if not signature_ok(header):
        raise DomainError(401, "bad_signature", "Signature was not accepted")


def parse_update(data: dict) -> dict | None:
    """Simulator body or a real Telegram Update. None when there is nothing to say."""
    if not isinstance(data, dict):
        return None
    if data.get("chat_id") is not None and "message" not in data and "callback_query" not in data:
        update_id = data.get("update_id")
        return {
            "chat_id": str(data["chat_id"]),
            "chat_type": data.get("chat_type") or "private",
            "text": str(data.get("text") or ""),
            "update_id": None if update_id is None else str(update_id),
            "callback": data.get("callback"),
            "callback_id": data.get("callback_id"),
            "message_id": data.get("message_id"),
            "media": data.get("media"),
        }
    if isinstance(data.get("callback_query"), dict):
        query = data["callback_query"]
        message = query.get("message") or {}
        chat = message.get("chat") or {}
        if chat.get("id") is None:
            return None
        return {
            "chat_id": str(chat["id"]),
            "chat_type": chat.get("type") or "private",
            "text": "",
            "update_id": str(data.get("update_id")),
            "callback": query.get("data"),
            "callback_id": query.get("id"),
            "message_id": message.get("message_id"),
            "media": None,
        }
    message = data.get("message") or data.get("edited_message")
    if not isinstance(message, dict):
        return None
    chat = message.get("chat") or {}
    if chat.get("id") is None:
        return None
    media = None
    if "location" in message:
        media = "location"
    elif any(kind in message for kind in ("voice", "audio", "video_note")):
        media = "voice"
    elif any(kind in message for kind in ("photo", "document", "sticker", "video")):
        media = "file"
    update_id = data.get("update_id")
    return {
        "chat_id": str(chat["id"]),
        "chat_type": chat.get("type") or "private",
        "text": str(message.get("text") or ""),
        "update_id": None if update_id is None else str(update_id),
        "callback": None,
        "callback_id": None,
        "message_id": message.get("message_id"),
        "media": media,
    }


def parse_incoming(data: dict) -> tuple[str, str, str | None] | None:
    parsed = parse_update(data)
    if parsed is None:
        return None
    return parsed["chat_id"], parsed["text"], parsed["update_id"]


def _visible(messages: list[dict]) -> str:
    return "\n".join(message["text"] for message in messages if message.get("text"))


def _buttons(message: dict) -> list[dict]:
    rows = []
    inline = []
    for button in message.get("buttons") or []:
        if button.get("url"):
            inline.append({"text": button["label"], "url": button["url"]})
        elif button.get("data") and message.get("keyboard") != "main":
            inline.append({"text": button["label"], "callback_data": str(button["data"])[:64]})
        else:
            rows.append(button["label"])
    markup = None
    if message.get("keyboard") == "main" and rows:
        pairs = [rows[index : index + 2] for index in range(0, len(rows), 2)]
        markup = {"keyboard": pairs, "resize_keyboard": True, "is_persistent": True}
    elif inline:
        pairs = [inline[index : index + 2] for index in range(0, len(inline), 2)]
        markup = {"inline_keyboard": pairs}
    return markup


def ingest(db: Session, event: dict) -> dict:
    chat_id = str(event["chat_id"])
    update_id = event.get("update_id")
    session = get_session(db, "telegram", session_key(chat_id))
    if update_id and session.last_update_id == update_id:
        return {"duplicate": True, "reply_text": "", "messages": [], "mode_label": "freeform"}
    result = turn(db, session, event, chat_id)
    messages = result.get("messages") or []
    if session.language == "ksl":
        messages = _with_ksl(db, session, messages)
    from app.modules.followup.telegram_phrase import phrase_messages

    messages = phrase_messages(messages, session.language or "en")
    session.last_update_id = None if update_id is None else str(update_id)
    session.updated_at = clock.now()
    reply = _visible(messages)
    log_outbound(db, session.public_id, "telegram", "reply", "freeform", reply)
    db.commit()
    flat_buttons = []
    for message in messages:
        for button in message.get("buttons") or []:
            if button.get("data"):
                flat_buttons.append({"id": str(button["data"])[:64], "label": button.get("label", "")})
    return {
        "duplicate": False,
        "reply_text": reply,
        "messages": messages,
        "buttons": flat_buttons,
        "mode_label": "freeform",
        "synthetic": True,
        "delete_message_ids": result.get("delete_message_ids") or [],
        "callback_id": event.get("callback_id"),
    }


def _with_ksl(db: Session, session, messages: list[dict]) -> list[dict]:
    from app.modules.followup.models import Enrolment
    from app.modules.tasks.service import create_task

    enrolment = None
    if session.public_id:
        enrolment = db.scalar(select(Enrolment).where(Enrolment.public_id == session.public_id))
    opened = False
    for message in messages:
        packet = for_channel(db, message.get("template_id") or "", message.get("text") or "", "telegram")
        if packet.get("available") and packet.get("video_url"):
            message["video_url"] = packet["video_url"]
            message["caption"] = packet.get("caption") or message.get("text")
        elif not opened and enrolment is not None and enrolment.case_id:
            create_task(
                db,
                task_type="followup_ksl",
                priority="high",
                case_id=enrolment.case_id,
                source="telegram",
            )
            opened = True
    return messages


def post_json(method: str, payload: dict) -> dict:
    token = present("token")
    if not token:
        return {"ok": True, "skipped": True}
    url = f"{API}/bot{token}/{method}"
    for attempt in (1, 2):
        response = httpx.post(url, json=payload, timeout=10.0)
        status = getattr(response, "status_code", 200)
        if status == 429 and attempt == 1:
            retry = 1
            if hasattr(response, "json"):
                body = response.json()
                retry = int((body.get("parameters") or {}).get("retry_after") or 1)
            time.sleep(min(retry, 2))
            continue
        if status in {400, 403}:
            body = response.json() if hasattr(response, "json") else {}
            return {"ok": False, "error_code": status, "description": body.get("description", "")}
        if hasattr(response, "raise_for_status"):
            response.raise_for_status()
        if hasattr(response, "json"):
            try:
                return response.json()
            except ValueError:
                return {"ok": True}
        return {"ok": True}
    return {"ok": False}


def deliver(db: Session, chat_id: str, result: dict) -> None:
    if result.get("duplicate"):
        return
    callback_id = result.get("callback_id")
    if callback_id:
        post_json("answerCallbackQuery", {"callback_query_id": callback_id})
    messages = result.get("messages") or []
    if not messages and result.get("reply_text"):
        messages = [{"text": result["reply_text"], "buttons": []}]
    if messages:
        post_json("sendChatAction", {"chat_id": chat_id, "action": "typing"})
    for message in messages:
        if message.get("video_url"):
            sent = post_json(
                "sendVideo",
                {
                    "chat_id": chat_id,
                    "video": message["video_url"],
                    "caption": message.get("caption") or message.get("text") or "",
                },
            )
        else:
            payload = {"chat_id": chat_id, "text": message.get("text") or ""}
            markup = _buttons(message)
            if markup:
                payload["reply_markup"] = markup
            sent = post_json("sendMessage", payload)
        if not sent.get("ok") and sent.get("error_code") in {400, 403}:
            description = (sent.get("description") or "").lower()
            if sent.get("error_code") == 403 or "not found" in description or "blocked" in description:
                mark_unreachable(db, chat_id)
                db.commit()
                return
    for message_id in result.get("delete_message_ids") or []:
        post_json("deleteMessage", {"chat_id": chat_id, "message_id": message_id})


def push_checkin(db: Session, enrolment) -> None:
    if enrolment.channel != "telegram":
        return
    vault = db.scalar(select(TelegramVault).where(TelegramVault.public_id == enrolment.public_id))
    if vault is None or not vault.chat_id or vault.unreachable:
        return
    if vault.paused_until is not None and vault.paused_until > clock.now():
        return
    session = get_session(db, "telegram", session_key(vault.chat_id))
    session.public_id = enrolment.public_id
    session.language = enrolment.language if enrolment.language in {"en", "sw", "ksl"} else "en"
    session.step = "checkin"
    messages = checkin_messages(session.language, tips=bool(vault.tips_opt_in))
    deliver(db, vault.chat_id, {"messages": messages, "duplicate": False})


def poll_once(db: Session, offset: int | None = None) -> int | None:
    """One getUpdates call for local dev. Turn the webhook off first.

    The Bot API does not deliver getUpdates while a webhook is set.
    """
    payload: dict = {"timeout": 0, "allowed_updates": ["message", "callback_query"]}
    if offset is not None:
        payload["offset"] = offset
    body = post_json("getUpdates", payload)
    next_offset = offset
    for update in body.get("result") or []:
        parsed = parse_update(update)
        if parsed is not None:
            result = ingest(db, parsed)
            if not result.get("duplicate"):
                deliver(db, parsed["chat_id"], result)
        if update.get("update_id") is not None:
            next_offset = int(update["update_id"]) + 1
    return next_offset


def command_payloads() -> list[dict]:
    from app.modules.followup.telegram_copy import flows

    commands = flows().get("commands") or []
    payloads = []
    for language, field in (("en", "description_en"), ("sw", "description_sw")):
        payloads.append(
            {
                "language_code": language,
                "commands": [
                    {"command": item["command"], "description": item[field]} for item in commands
                ],
            }
        )
    return payloads


def slip_link(db: Session, public_id: str) -> str:
    return link_url(mint_link(db, public_id))
