"""Menu flow for Telegram. Safety, ID checks, and tasks stay in the core."""

from __future__ import annotations

import hashlib
import re
import secrets
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.modules.audit import service as audit
from app.modules.followup import access
from app.modules.followup.conversation import classify, respond
from app.modules.followup.ids import parse_public_id
from app.modules.followup.models import ChannelSession, Enrolment
from app.modules.followup.telegram_copy import button_rows, clinics, label_map, line
from app.modules.followup.telegram_env import present
from app.modules.followup.telegram_models import TelegramChat, TelegramDeepLink, TelegramVault
from app.modules.ksl.models import KslFacilityFlag
from app.modules.pathways.models import CareCase
from app.modules.tasks.service import create_task

TOKEN_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"
EMOJI = re.compile(
    "[\U0001f300-\U0001faff\u2600-\u27bf\u2705\u274c\u2764\ufe0f\u200d]+",
    re.UNICODE,
)
URGENT_KEYS = {"worse", "unsure", "danger"}
STOP_WORDS = {"stop", "simama", "/stop"}
START_WORDS = {"start", "anza", "/start"}
SETUP = {"language", "privacy", "id", "code", "declined"}


def session_key(chat_id: str) -> str:
    return hashlib.sha256(f"telegram:{chat_id}".encode()).hexdigest()[:40]


def mint_link(db: Session, public_id: str, *, hours: int = 24) -> str:
    token = "".join(secrets.choice(TOKEN_ALPHABET) for _ in range(22))
    db.add(
        TelegramDeepLink(
            token=token,
            public_id=public_id,
            expires_at=clock.now() + timedelta(hours=hours),
            used_at=None,
        )
    )
    db.flush()
    return token


def link_url(token: str) -> str:
    name = present("username") or "LoopieCareBot"
    return f"https://t.me/{name}?start={token}"


def _audit(db: Session, enrolment: Enrolment | None, label: str) -> None:
    audit.record(
        db,
        actor=None,
        action="telegram.turn",
        entity_type="followup",
        entity_id=enrolment.id if enrolment else None,
        patient_id=enrolment.patient_id if enrolment else None,
        detail={"label": label, "channel": "telegram"},
    )


def _enrolment(db: Session, session: ChannelSession) -> Enrolment | None:
    if not session.public_id:
        return None
    return db.scalar(select(Enrolment).where(Enrolment.public_id == session.public_id))


def _case(db: Session, enrolment: Enrolment | None) -> CareCase | None:
    if enrolment is None or enrolment.case_id is None:
        return None
    return db.get(CareCase, enrolment.case_id)


def _chat(db: Session, key: str) -> TelegramChat:
    row = db.scalar(select(TelegramChat).where(TelegramChat.session_key == key))
    if row:
        return row
    row = TelegramChat(session_key=key, group_noted=False, pending_token="")
    db.add(row)
    db.flush()
    return row


def _vault(db: Session, public_id: str | None) -> TelegramVault | None:
    if not public_id:
        return None
    return db.scalar(select(TelegramVault).where(TelegramVault.public_id == public_id))


def _bind(db: Session, public_id: str, chat_id: str) -> TelegramVault:
    others = db.scalars(select(TelegramVault).where(TelegramVault.chat_id == str(chat_id))).all()
    for other in others:
        if other.public_id != public_id:
            other.chat_id = None
    row = _vault(db, public_id)
    if row is None:
        row = TelegramVault(public_id=public_id, chat_id=str(chat_id), pending_labels="")
        db.add(row)
    else:
        row.chat_id = str(chat_id)
        row.unreachable = False
    db.flush()
    return row


def _unbind(db: Session, public_id: str | None) -> None:
    row = _vault(db, public_id)
    if row is not None:
        row.chat_id = None
        db.flush()


def mark_unreachable(db: Session, chat_id: str) -> None:
    row = db.scalar(select(TelegramVault).where(TelegramVault.chat_id == str(chat_id)))
    if row is None or row.unreachable:
        return
    row.unreachable = True
    enrolment = db.scalar(select(Enrolment).where(Enrolment.public_id == row.public_id))
    if enrolment and enrolment.case_id:
        create_task(
            db,
            task_type="followup_unreachable",
            priority="high",
            case_id=enrolment.case_id,
            source="telegram",
        )
    _audit(db, enrolment, "unreachable")
    db.flush()


def _msg(key: str, language: str, *, buttons=None, keyboard=None, urgent=False, **fmt) -> dict:
    text = line(key, language, **fmt)
    if urgent or key in URGENT_KEYS:
        text = EMOJI.sub("", text).strip()
        urgent = True
    return {
        "text": text,
        "template_id": key,
        "urgent": urgent,
        "buttons": buttons or [],
        "keyboard": keyboard,
    }


def _inline(menu: str) -> list[dict]:
    return [item for row in button_rows(menu, inline=True) for item in row]


def _reply_keyboard() -> list[dict]:
    return [item for row in button_rows("main", inline=False) for item in row]


def _with_menu(message: dict) -> dict:
    message["keyboard"] = "main"
    message["buttons"] = _reply_keyboard()
    return message


def _clinic_for(enrolment: Enrolment | None) -> dict:
    areas = clinics().get("areas") or []
    chosen = areas[0]
    area = (enrolment.area_label if enrolment else "") or ""
    for item in areas:
        if item["id"] in area.lower() or item["label"].lower() in area.lower():
            chosen = item
            break
    place = chosen["clinics"][0]
    return {
        "clinic": place["name"],
        "hours": place["hours"],
        "facility_key": place["name"].lower().replace(" ", "-"),
    }


def _journey(enrolment: Enrolment | None, case: CareCase | None, language: str) -> str:
    arrived = case is not None and case.state == "arrived"
    visit = "✅" if enrolment and enrolment.reported_visit else "🔵"
    clinic_mark = "✅" if arrived else "⚪"
    return line(
        "journey",
        language,
        visit_mark=visit,
        clinic_mark=clinic_mark,
    )


def _task(db, enrolment: Enrolment | None, task_type: str, priority: str) -> None:
    if enrolment is None or enrolment.case_id is None:
        return
    create_task(
        db,
        task_type=task_type,
        priority=priority,
        case_id=enrolment.case_id,
        source="telegram",
    )


def _reject(language: str) -> list[dict]:
    return [_msg("id_rejected", language)]


def _consume_token(db: Session, chat: TelegramChat, public_id: str) -> None:
    token = chat.pending_token
    if not token:
        return
    row = db.scalar(select(TelegramDeepLink).where(TelegramDeepLink.token == token))
    if row and row.public_id == public_id and row.used_at is None:
        row.used_at = clock.now()
    chat.pending_token = ""


def _remember_token(db: Session, chat: TelegramChat, token: str) -> bool:
    row = db.scalar(select(TelegramDeepLink).where(TelegramDeepLink.token == token))
    if row is None or row.used_at is not None or row.expires_at < clock.now():
        return False
    if row.token == row.public_id:
        return False
    chat.pending_token = row.token
    return True


def _stop(db, session, enrolment, language) -> list[dict]:
    if enrolment is not None:
        enrolment.messages_stopped = True
    _unbind(db, session.public_id)
    session.public_id = None
    session.step = "id"
    _audit(db, enrolment, "stop")
    return [_msg("stop_ack", language)]


def _safety(db, session, enrolment, text: str) -> list[dict] | None:
    label = classify(text or "")
    if label in {"danger", "distress"}:
        _task(db, enrolment, "followup_urgent", "urgent")
        if enrolment is not None and label == "danger":
            enrolment.symptom_flag = "worse"
        _audit(db, enrolment, label)
        return [_msg("danger", session.language, urgent=True)]
    if label == "diagnosis":
        _task(db, enrolment, "followup_review", "high")
        _audit(db, enrolment, "diagnosis_request")
        return [_msg("refuse_diagnosis", session.language)]
    if label == "skip":
        _task(db, enrolment, "followup_review", "high")
        _audit(db, enrolment, "skip_request")
        return [_msg("refuse_skip", session.language)]
    return None


def _language_pick(session, code: str) -> list[dict] | None:
    picked = {"lang:en": "en", "lang:sw": "sw", "lang:ksl": "ksl", "1": "en", "2": "sw", "3": "ksl"}
    language = picked.get(code)
    if language is None:
        return None
    session.language = language
    session.step = "privacy"
    _buttons = _inline("privacy")
    return [_msg("privacy", language, buttons=_buttons)]


def _on_code(db, session, chat, chat_id: str, text: str) -> list[dict]:
    language = session.language
    if access.locked("client", session.session_key, clock.now()):
        return _reject(language)
    if not access.code_ok(db, session.public_id or "", text.strip(), session.session_key):
        session.public_id = None
        session.step = "id"
        _audit(db, None, "code_rejected")
        return _reject(language)
    enrolment = _enrolment(db, session)
    if enrolment is None:
        session.step = "id"
        return _reject(language)
    enrolment.messages_stopped = False
    _bind(db, enrolment.public_id, chat_id)
    _consume_token(db, chat, enrolment.public_id)
    session.step = "ready"
    _audit(db, enrolment, "bound")
    place = _clinic_for(enrolment)
    return [
        _msg("tour_1", language),
        _msg("tour_2", language),
        _with_menu(_msg("tour_3", language)),
        _msg("next_step", language, clinic=place["clinic"], hours=place["hours"]),
    ]


def _on_id(db, session, text: str) -> tuple[list[dict], bool]:
    language = session.language
    if access.locked("client", session.session_key, clock.now()):
        return _reject(language), False
    public_id = parse_public_id(text)
    found = None
    if public_id:
        found = db.scalar(select(Enrolment).where(Enrolment.public_id == public_id))
    if found is None:
        access._fail("client", session.session_key, clock.now())
        _audit(db, None, "id_rejected")
        return _reject(language), True
    if chat_token_mismatch(db, session, found.public_id):
        access._fail("client", session.session_key, clock.now())
        _audit(db, None, "id_rejected")
        return _reject(language), True
    access.issue_code(db, found.public_id)
    session.public_id = found.public_id
    session.step = "code"
    message = _msg("ask_code", language)
    code = access.dev_code(found.public_id)
    if code:
        message["text"] = f"{message['text']}\nSIMULATED code: {code}"
    _audit(db, found, "ask_code")
    return [message], True


def chat_token_mismatch(db: Session, session: ChannelSession, public_id: str) -> bool:
    chat = db.scalar(select(TelegramChat).where(TelegramChat.session_key == session.session_key))
    if chat is None or not chat.pending_token:
        return False
    row = db.scalar(select(TelegramDeepLink).where(TelegramDeepLink.token == chat.pending_token))
    return row is not None and row.public_id != public_id


def _ready_action(db, session, enrolment, action: str) -> list[dict]:
    language = session.language or "en"
    case = _case(db, enrolment)
    vault = _vault(db, session.public_id)
    if action in {"next", "menu:next", "status"}:
        if case is not None and case.state == "arrived" and vault is not None and not vault.celebrated:
            vault.celebrated = True
            _audit(db, enrolment, "celebrate")
            return [_with_menu(_msg("celebrate", language))]
        place = _clinic_for(enrolment)
        text = _journey(enrolment, case, language) + "\n" + line("next_step", language, clinic=place["clinic"], hours=place["hours"])
        message = _with_menu(_msg("next_step", language, clinic=place["clinic"], hours=place["hours"]))
        message["text"] = text
        _audit(db, enrolment, "next_step")
        return [message]
    if action in {"clinic", "menu:clinic"}:
        session.step = "clinic"
        _audit(db, enrolment, "clinic")
        return [_clinic_menu(language)]
    if action in {"help", "menu:help"}:
        session.step = "help"
        _audit(db, enrolment, "help")
        return [_msg("help_intro", language, buttons=_inline("help"))]
    if action in {"visit", "menu:visit"}:
        session.step = "visit"
        _audit(db, enrolment, "visit")
        return [_msg("visit_bring", language, buttons=_inline("visit"))]
    if action in {"language", "menu:lang"}:
        session.step = "language"
        return [_msg("greeting", language, buttons=_inline("language"))]
    if action in {"settings", "menu:set"}:
        session.step = "settings"
        return [_msg("settings_intro", language, buttons=_inline("settings"))]
    if action in {"checkin", "chk:help"}:
        session.step = "help"
        return [_msg("help_intro", language, buttons=_inline("help"))]
    if action == "chk:not":
        session.step = "barrier"
        if vault is not None:
            vault.pending_labels = ""
        return [_msg("barrier_ask", language, buttons=_inline("barriers"))]
    if action == "chk:yes" or action in {"been", "i went", "i have been"}:
        if enrolment is not None:
            respond(db, enrolment, "telegram", language, "been")
        _audit(db, enrolment, "reported_visit")
        session.step = "ready"
        return [_with_menu(_msg("been", language)), _msg("which_day", language)]
    if action in {"sym:same", "same"}:
        if enrolment is not None:
            respond(db, enrolment, "telegram", language, "same")
        session.step = "ready"
        _audit(db, enrolment, "same")
        return [_with_menu(_msg("same", language))]
    if action in {"sym:better", "better"}:
        if enrolment is not None:
            respond(db, enrolment, "telegram", language, "better")
        session.step = "ready"
        _audit(db, enrolment, "better")
        return [_with_menu(_msg("better", language))]
    if action in {"sym:worse", "worse"}:
        if enrolment is not None:
            respond(db, enrolment, "telegram", language, "worse")
        else:
            _task(db, enrolment, "followup_urgent", "urgent")
        session.step = "ready"
        _audit(db, enrolment, "worse")
        return [_msg("worse", language, urgent=True), _clinic_menu(language, urgent=True)]
    if action in {"sym:unsure", "not sure"}:
        if enrolment is not None:
            enrolment.symptom_flag = "unsure"
        _task(db, enrolment, "followup_urgent", "urgent")
        session.step = "ready"
        _audit(db, enrolment, "unsure")
        return [_msg("unsure", language, urgent=True), _clinic_menu(language, urgent=True)]
    return []


def _clinic_menu(language: str, *, urgent: bool = False) -> dict:
    buttons = []
    for area in (clinics().get("areas") or [])[:3]:
        buttons.append({"label": area["label"], "data": f"area:{area['id']}"})
    buttons.append({"label": "Location is off", "data": "loc:off"})
    message = _msg("clinic_intro", language, buttons=buttons, urgent=urgent)
    return message


def _area_cards(language: str, area_id: str) -> list[dict]:
    for area in clinics().get("areas") or []:
        if area["id"] != area_id:
            continue
        cards = []
        for place in area["clinics"][:3]:
            buttons = [{"label": "Directions", "url": place["directions"], "data": "dir"}]
            cards.append(
                _msg(
                    "clinic_card",
                    language,
                    buttons=buttons,
                    name=place["name"],
                    hours=place["hours"],
                    directions=place["directions"],
                )
            )
        return cards
    return [_msg("unclear", language)]


def _help_action(db, session, enrolment, action: str) -> list[dict]:
    language = session.language or "en"
    vault = _vault(db, session.public_id)
    cards = {
        "help:fear": "help_fear",
        "help:cost": "help_cost",
        "help:transport": "help_transport",
        "help:where": "help_where",
        "help:sign": "help_sign",
    }
    if action in cards:
        if vault is not None:
            vault.pending_labels = action.split(":", 1)[1]
        if action == "help:sign":
            place = _clinic_for(enrolment)
            _set_interpreter(db, place["facility_key"])
            _audit(db, enrolment, "interpreter")
        confirm = [{"label": "Ask a person to help", "data": "help:yes"}]
        return [_msg(cards[action], language, buttons=confirm)]
    if action == "help:person" or action == "help:yes":
        kind = "followup_review" if action == "help:person" else "followup_barrier"
        _task(db, enrolment, kind, "normal")
        if enrolment is not None and vault is not None and vault.pending_labels:
            enrolment.barrier_label = vault.pending_labels[:40]
        session.step = "ready"
        _audit(db, enrolment, "human")
        return [_with_menu(_msg("help_person", language))]
    return []


def _set_interpreter(db: Session, facility_key: str) -> None:
    row = db.scalar(select(KslFacilityFlag).where(KslFacilityFlag.facility_key == facility_key))
    today = clock.now().date().isoformat()
    if row is None:
        db.add(KslFacilityFlag(facility_key=facility_key, interpreter_available=True, recorded_on=today))
    else:
        row.interpreter_available = True
        row.recorded_on = today
    db.flush()


def _barrier_action(db, session, enrolment, action: str) -> list[dict]:
    language = session.language or "en"
    vault = _vault(db, session.public_id)
    labels = {"bar:fear", "bar:cost", "bar:transport", "bar:where", "bar:other"}
    if action in labels and vault is not None:
        current = [item for item in vault.pending_labels.split(",") if item]
        name = action.split(":", 1)[1]
        if name not in current:
            current.append(name)
        vault.pending_labels = ",".join(current)
        key = f"barrier_{name}"
        return [_msg(key, language, buttons=_inline("barriers"))]
    if action == "bar:done":
        if vault is not None and vault.pending_labels:
            if enrolment is not None:
                enrolment.barrier_label = vault.pending_labels.split(",")[0]
            _task(db, enrolment, "followup_barrier", "normal")
            _audit(db, enrolment, "barrier_confirmed")
            session.step = "symptom"
            return [
                _msg("barrier_sent", language),
                _msg("symptom_ask", language, buttons=_inline("symptoms")),
            ]
        session.step = "symptom"
        return [_msg("symptom_ask", language, buttons=_inline("symptoms"))]
    return []


def _settings_action(db, session, enrolment, action: str) -> list[dict]:
    language = session.language or "en"
    vault = _vault(db, session.public_id)
    if action == "set:pause" and vault is not None:
        vault.paused_until = clock.now() + timedelta(days=7)
        _audit(db, enrolment, "pause")
        return [_with_menu(_msg("pause_ack", language))]
    if action == "set:stop":
        return _stop(db, session, enrolment, language)
    if action == "set:privacy":
        return [_msg("privacy_long", language, buttons=_inline("settings"))]
    if action == "set:unbind":
        _unbind(db, session.public_id)
        session.public_id = None
        session.step = "id"
        _audit(db, enrolment, "unbind")
        return [_msg("unbind_ack", language)]
    if action == "set:tips" and vault is not None:
        vault.tips_opt_in = not vault.tips_opt_in
        _audit(db, enrolment, "tips")
        if vault.tips_opt_in:
            return [_msg("tip", language)]
        return [_with_menu(_msg("settings_intro", language))]
    if action == "set:myth":
        buttons = [
            {"label": "Fact", "data": "myth:fact"},
            {"label": "Myth", "data": "myth:myth"},
        ]
        return [_msg("myth_q", language, buttons=buttons)]
    if action in {"myth:fact", "myth:myth"}:
        return [_with_menu(_msg("myth_answer", language))]
    return []


def _command(text: str) -> tuple[str, str]:
    cleaned = (text or "").strip()
    if not cleaned.startswith("/"):
        return "", cleaned
    head, _, rest = cleaned.partition(" ")
    return head.split("@", 1)[0].lower(), rest.strip()


def _action_code(text: str, callback: str | None) -> str:
    if callback:
        return callback.strip()
    low = (text or "").strip().lower()
    if low in label_map():
        return label_map()[low]
    aliases = {
        "been": "been",
        "i have been": "been",
        "i went": "been",
        "not yet": "chk:not",
        "same": "sym:same",
        "better": "sym:better",
        "worse": "sym:worse",
        "not sure": "sym:unsure",
    }
    return aliases.get(low, low)


def turn(db: Session, session: ChannelSession, event: dict, chat_id: str) -> dict:
    chat = _chat(db, session.session_key)
    language = session.language or "en"
    if event.get("chat_type") not in {None, "", "private"}:
        if chat.group_noted:
            return {"messages": [], "delete_message_ids": []}
        chat.group_noted = True
        _audit(db, None, "group")
        return {"messages": [_msg("group_once", "en")], "delete_message_ids": []}

    media = event.get("media")
    if media == "location":
        _audit(db, _enrolment(db, session), "location_ignored")
        return {"messages": [_with_menu(_msg("location_off", language))], "delete_message_ids": []}
    if media:
        _audit(db, _enrolment(db, session), "media_ignored")
        buttons = [{"label": "Talk to a person", "data": "help:person"}]
        return {"messages": [_msg("cant_media", language, buttons=buttons)], "delete_message_ids": []}

    text = event.get("text") or ""
    command, arg = _command(text)
    callback = event.get("callback")
    delete_ids = []
    enrolment = _enrolment(db, session)

    if command == "/start" and arg:
        if not _remember_token(db, chat, arg):
            session.step = "id"
            return {"messages": [_msg("token_bad", language)], "delete_message_ids": []}
        session.step = "language"

    safety = _safety(db, session, enrolment, text if not callback else "")
    if safety is not None:
        return {"messages": safety, "delete_message_ids": []}

    low = text.strip().lower()
    if command == "/stop" or low in STOP_WORDS or callback == "set:stop":
        return {"messages": _stop(db, session, enrolment, language), "delete_message_ids": []}

    if enrolment is not None and enrolment.messages_stopped and low not in START_WORDS and command != "/start":
        return {"messages": [_msg("stop_ack", language)], "delete_message_ids": []}

    if command == "/start" or low in START_WORDS:
        if (enrolment is not None and enrolment.messages_stopped) or session.step == "id":
            session.public_id = None
            session.step = "id"
            return {"messages": [_msg("start_verify", language)], "delete_message_ids": []}
        if session.step in {"ready", "checkin", "barrier", "symptom"} and command != "/start":
            pass
        elif session.step == "language" or command == "/start":
            session.step = "language"
            return {
                "messages": [_msg("greeting", "en", buttons=_inline("language"))],
                "delete_message_ids": [],
            }

    if command == "/language" or (session.step == "language" and not callback and not text):
        session.step = "language"
        return {"messages": [_msg("greeting", language, buttons=_inline("language"))], "delete_message_ids": []}

    if session.step == "language":
        code = callback or label_map().get(low, low)
        picked = _language_pick(session, code)
        if picked:
            return {"messages": picked, "delete_message_ids": []}
        return {"messages": [_msg("greeting", "en", buttons=_inline("language"))], "delete_message_ids": []}

    if session.step == "privacy":
        code = callback or low
        if code in {"ok:yes", "ok", "yes"}:
            session.step = "id"
            return {"messages": [_msg("ask_id", language)], "delete_message_ids": []}
        if code in {"ok:no", "no", "no thanks"}:
            session.step = "declined"
            if enrolment is not None:
                enrolment.messages_stopped = True
            _audit(db, enrolment, "declined")
            return {"messages": [_msg("declined", language)], "delete_message_ids": []}
        return {"messages": [_msg("privacy", language, buttons=_inline("privacy"))], "delete_message_ids": []}

    if session.step in {"id", "declined"} or (enrolment and enrolment.messages_stopped and session.step == "id"):
        if session.step == "declined" and low not in START_WORDS:
            return {"messages": [_msg("declined", language)], "delete_message_ids": []}
        messages, attempted = _on_id(db, session, text)
        if attempted and event.get("message_id"):
            delete_ids.append(event["message_id"])
        return {"messages": messages, "delete_message_ids": delete_ids}

    if session.step == "code":
        return {"messages": _on_code(db, session, chat, chat_id, text), "delete_message_ids": []}

    if session.public_id is None or enrolment is None:
        session.step = "id"
        return {"messages": [_msg("ask_id", language)], "delete_message_ids": []}

    if command == "/menu":
        session.step = "ready"
        return {"messages": [_with_menu(_msg("tour_1", language))], "delete_message_ids": []}
    if command == "/status":
        return {"messages": _ready_action(db, session, enrolment, "next"), "delete_message_ids": []}
    if command == "/help":
        return {"messages": _ready_action(db, session, enrolment, "help"), "delete_message_ids": []}

    action = _action_code(text, callback)
    if session.step == "barrier" or action.startswith("bar:"):
        found = _barrier_action(db, session, enrolment, action)
        if found:
            return {"messages": found, "delete_message_ids": []}
    if session.step == "clinic" or action.startswith("area:") or action == "loc:off":
        if action == "loc:off":
            return {"messages": [_with_menu(_msg("location_off", language))], "delete_message_ids": []}
        if action.startswith("area:"):
            return {"messages": _area_cards(language, action.split(":", 1)[1]), "delete_message_ids": []}
    if session.step == "help" or action.startswith("help:"):
        found = _help_action(db, session, enrolment, action)
        if found:
            return {"messages": found, "delete_message_ids": []}
    if session.step == "visit" or action.startswith("vis:"):
        visit_keys = {
            "vis:bring": "visit_bring",
            "vis:time": "visit_time",
            "vis:someone": "visit_someone",
            "vis:fees": "visit_fees",
            "vis:scared": "visit_scared",
        }
        if action in visit_keys:
            _audit(db, enrolment, action)
            return {
                "messages": [_msg(visit_keys[action], language, buttons=_inline("visit"))],
                "delete_message_ids": [],
            }
    if session.step == "settings" or action.startswith(("set:", "myth:")):
        found = _settings_action(db, session, enrolment, action)
        if found:
            return {"messages": found, "delete_message_ids": []}
    if session.step == "symptom" or action.startswith("sym:"):
        found = _ready_action(db, session, enrolment, action)
        if found:
            return {"messages": found, "delete_message_ids": []}
    if action in {"chk:yes", "chk:not", "chk:help"} or session.step == "checkin":
        if session.step == "checkin" and action in {"", low}:
            return {
                "messages": [_msg("checkin", language, buttons=_inline("checkin"))],
                "delete_message_ids": [],
            }
        found = _ready_action(db, session, enrolment, action)
        if found:
            return {"messages": found, "delete_message_ids": []}
    found = _ready_action(db, session, enrolment, action)
    if found:
        return {"messages": found, "delete_message_ids": []}
    _task(db, enrolment, "followup_review", "normal")
    _audit(db, enrolment, "unclear")
    unclear = _with_menu(_msg("unclear", language))
    return {"messages": [unclear], "delete_message_ids": []}


def checkin_messages(language: str, *, tips: bool) -> list[dict]:
    messages = [_msg("checkin", language if language in {"en", "sw"} else "en", buttons=_inline("checkin"))]
    if tips:
        messages.append(_msg("tip", language if language in {"en", "sw"} else "en"))
    return messages
