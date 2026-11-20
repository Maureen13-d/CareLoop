"""Simulated USSD and SMS.

Screens and texts stay short and discreet: no finding, no illness name. A real
short code is not connected. *XYZ# is a placeholder.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.modules.assistant.schemas import AssistantRequest
from app.modules.assistant.service import handle_message
from app.modules.assistant.text import normalise
from app.modules.channels.models import SmsMessage, SmsOptOut, UssdSession
from app.modules.tasks.service import create_task, should_open_task

DEMO_HANDSET = "+254700000101"
SMS_LIMIT = 160

HOME = "CareLoop\n1 Next step\n2 A question\n3 A worry\n4 My visit\n5 Call me\n6 Talk now"
WORRY = (
    "What worries you most?\n1 Fear or pain\n2 Cost\n3 Getting there\n4 Privacy\n5 Not sure\n0 Back"
)
NEXT_STEP = (
    "Your next step is a visit with a health worker. "
    "A navigator can help you plan it. Choose 5 for a call."
)
VISIT = (
    "If a visit is booked you will get a short text with the time and place. "
    "Reply 1 to confirm, 2 to change, 3 for help."
)
ASK = "Type a short question, then send."
CHOOSE = "Choose 1 to 6.\n" + HOME

CONFIRM = "Thank you. You confirmed the visit. A short reminder will follow."
CHANGE = "Okay. A navigator will contact you to change the time."
HELP = "A navigator will contact you. Reply STOP at any time to stop messages."

# Opt-in maternal check-in. The cervical home menu is unchanged.
MATERNAL_STEPS = (
    ("m_bleed", "Any bleeding?\n1 Yes\n2 No", "bleeding", {"1": "yes"}),
    ("m_head", "Head pain?\n1 Severe\n2 Mild\n3 No", "headache", {"1": "severe", "2": "mild"}),
    ("m_vis", "Blurred vision?\n1 Yes\n2 No", "vision", {"1": "blurred"}),
    ("m_swell", "Swelling of face or hands?\n1 Yes\n2 No", "swelling", {"1": "yes"}),
    ("m_pain", "Pain high in the belly?\n1 Yes\n2 No", "pain", {"1": "upper"}),
    ("m_move", "Movement?\n1 None\n2 Less\n3 Same", "movement", {"1": "none", "2": "less"}),
    ("m_fever", "Fever?\n1 With weakness\n2 Yes\n3 No", "fever", {"1": "severe", "2": "yes"}),
    ("m_fluid", "Fluid leaking?\n1 With fever\n2 Yes\n3 No", "fluid", {"1": "fever", "2": "yes"}),
    ("m_breath", "Hard to breathe?\n1 Yes\n2 No", "breathing", {"1": "yes"}),
    ("m_mood", "How do you feel?\n1 Unsafe\n2 Low\n3 Okay", "mood", {"1": "unsafe", "2": "low"}),
)


def _fit(text: str, limit: int = SMS_LIMIT) -> str:
    text = " ".join(text.split()) if "\n" not in text else text
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "."


def _session(db: Session, session_id: str, phone_ref: str) -> UssdSession:
    row = db.get(UssdSession, session_id)
    if row is None:
        row = UssdSession(id=session_id, phone_ref=phone_ref, menu="home", updated_at=clock.now())
        db.add(row)
        db.flush()
    row.phone_ref = phone_ref
    row.updated_at = clock.now()
    if row.scratch is None:
        row.scratch = ""
    return row


def _maternal_step(db: Session, row: UssdSession, choice: str) -> str:
    names = [step[0] for step in MATERNAL_STEPS]
    try:
        index = names.index(row.menu)
    except ValueError:
        row.menu = "home"
        return CHOOSE
    _name, _prompt, key, answers = MATERNAL_STEPS[index]
    picked = answers.get(choice)
    if picked:
        row.scratch = f"{row.scratch or ''}{key}={picked};"
    if choice not in answers and choice not in {"2", "3"}:
        return _prompt
    if index + 1 < len(MATERNAL_STEPS):
        row.menu = MATERNAL_STEPS[index + 1][0]
        return MATERNAL_STEPS[index + 1][1]
    parsed: dict[str, str] = {}
    for part in (row.scratch or "").split(";"):
        if "=" in part:
            left, right = part.split("=", 1)
            parsed[left] = right
    if not parsed:
        parsed = {"all_clear": "yes"}
    response = handle_message(
        AssistantRequest(channel="ussd", pathway="maternal", checkin=parsed, language="en")
    )
    _maybe_task(db, response)
    row.menu = "home"
    row.scratch = ""
    return response.reply_text


def _maybe_task(db: Session, response) -> None:
    if should_open_task(response) and response.suggested_task:
        create_task(
            db,
            task_type=response.suggested_task.type,
            priority=response.suggested_task.priority,
            source="channel",
        )


def handle_ussd(db: Session, session_id: str, phone_ref: str, text: str) -> str:
    row = _session(db, session_id, phone_ref)
    choice = (text or "").strip()
    menu = row.menu

    if choice in {"", "0", "*XYZ#", "*xyz#"}:
        row.menu = "home"
        screen = HOME
    elif menu == "worry" and choice in {"1", "2", "3", "4", "5"}:
        response = handle_message(
            AssistantRequest(channel="ussd", menu_choice=choice, menu_context="worry_menu")
        )
        _maybe_task(db, response)
        row.menu = "home"
        screen = response.reply_text
    elif menu == "question" and choice not in {"0"}:
        response = handle_message(AssistantRequest(channel="ussd", text=choice))
        _maybe_task(db, response)
        row.menu = "home"
        screen = response.reply_text
    elif menu == "home" and choice == "1":
        row.menu = "home"
        screen = NEXT_STEP
    elif menu == "home" and choice == "2":
        row.menu = "question"
        screen = ASK
    elif menu == "home" and choice == "3":
        row.menu = "worry"
        screen = WORRY
    elif menu == "home" and choice == "4":
        row.menu = "home"
        screen = VISIT
    elif menu == "home" and choice == "5":
        response = handle_message(AssistantRequest(channel="ussd", text="call me"))
        _maybe_task(db, response)
        row.menu = "home"
        screen = response.reply_text
    elif menu == "home" and choice == "6":
        response = handle_message(AssistantRequest(channel="ussd", text="talk to someone"))
        _maybe_task(db, response)
        row.menu = "home"
        screen = response.reply_text
    elif menu == "home" and choice.upper() == "M":
        row.menu = MATERNAL_STEPS[0][0]
        row.scratch = ""
        screen = MATERNAL_STEPS[0][1]
    elif menu.startswith("m_"):
        screen = _maternal_step(db, row, choice)
    else:
        row.menu = "home"
        screen = CHOOSE

    db.commit()
    return _fit(screen, 182)


def _save(db: Session, phone_ref: str, direction: str, body: str, status: str) -> SmsMessage:
    message = SmsMessage(
        phone_ref=phone_ref,
        direction=direction,
        body=_fit(body),
        status=status,
        created_at=clock.now(),
    )
    db.add(message)
    db.flush()
    return message


def _opted_out(db: Session, phone_ref: str) -> bool:
    return db.get(SmsOptOut, phone_ref) is not None


def inbound_sms(db: Session, phone_ref: str, text: str) -> SmsMessage | None:
    """Record an inbound text and, when allowed, one discreet reply."""
    body = text.strip()
    _save(db, phone_ref, "in", body, "received")
    key = normalise(body)

    if _opted_out(db, phone_ref) and key != "start":
        db.commit()
        return None

    if key == "start":
        row = db.get(SmsOptOut, phone_ref)
        if row:
            db.delete(row)
        reply = _save(db, phone_ref, "out", "You will receive messages again.", "delivered")
        db.commit()
        return reply

    if key == "stop":
        if not _opted_out(db, phone_ref):
            db.add(SmsOptOut(phone_ref=phone_ref, opted_out_at=clock.now()))
        response = handle_message(AssistantRequest(channel="sms", text="STOP"))
        reply = _save(db, phone_ref, "out", response.reply_text, "delivered")
        db.commit()
        return reply

    if key.startswith(("m ", "check ")):
        language = "sw" if key.startswith(("m sw", "check sw")) else "en"
        response = handle_message(
            AssistantRequest(channel="sms", text=body, pathway="maternal", language=language)
        )
        _maybe_task(db, response)
        reply_text = response.reply_text
    elif key == "1":
        reply_text = CONFIRM
    elif key == "2":
        create_task(db, task_type="appointment_change", priority="normal", source="channel")
        reply_text = CHANGE
    elif key == "3":
        create_task(db, task_type="navigator_callback", priority="normal", source="channel")
        reply_text = HELP
    else:
        response = handle_message(AssistantRequest(channel="sms", text=body))
        _maybe_task(db, response)
        reply_text = response.reply_text

    reply = _save(db, phone_ref, "out", reply_text, "delivered")
    db.commit()
    return reply


def mark_undelivered(db: Session, message_id: int) -> SmsMessage:
    from app.core.errors import DomainError

    message = db.get(SmsMessage, message_id)
    if message is None or message.direction != "out":
        raise DomainError(404, "not_found", "Outbound message not found")
    message.status = "undelivered"
    create_task(db, task_type="sms_undelivered", priority="high", source="channel")
    db.commit()
    return message


def list_messages(db: Session, phone_ref: str | None, limit: int = 40) -> list[SmsMessage]:
    stmt = select(SmsMessage).order_by(SmsMessage.id.desc()).limit(limit)
    if phone_ref:
        stmt = stmt.where(SmsMessage.phone_ref == phone_ref)
    rows = list(db.scalars(stmt).all())
    rows.reverse()
    return rows


def seed_reminder(db: Session, phone_ref: str = DEMO_HANDSET) -> SmsMessage | None:
    existing = db.scalar(select(SmsMessage.id).where(SmsMessage.phone_ref == phone_ref))
    if existing:
        return None
    message = _save(
        db,
        phone_ref,
        "out",
        "CareLoop: a visit is set for Tue 10:00 at Demo Clinic. "
        "Reply 1 to confirm, 2 to change, 3 for help. STOP to opt out.",
        "delivered",
    )
    db.commit()
    return message
