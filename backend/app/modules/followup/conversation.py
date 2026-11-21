"""One conversation core for web, Telegram, USSD, and the guide.

Order: safety, then menu lines, then (web only) a short approved passage.
Nothing here is generated. Patient text is never written to the audit log.
"""

import re
from datetime import timedelta
from functools import wraps

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.modules.audit import service as audit
from app.modules.followup.models import ChannelSession, Enrolment, Outbound
from app.modules.followup.texts import fit, lexicon, line
from app.modules.pathways.models import CareCase
from app.modules.tasks.service import create_task

MENU = {
    "1": "been",
    "been": "been",
    "i have been": "been",
    "nimeenda": "been",
    "2": "not_yet",
    "not yet": "not_yet",
    "bado": "not_yet",
    "3": "same",
    "same": "same",
    "ile ile": "same",
    "4": "better",
    "better": "better",
    "bora": "better",
    "5": "worse",
    "worse": "worse",
    "mbaya": "worse",
    "fear": "fear",
    "hofu": "fear",
    "cost": "cost",
    "gharama": "cost",
    "transport": "transport",
    "fare": "transport",
    "nauli": "transport",
    "stigma": "stigma",
    "aibu": "stigma",
    "where": "where",
    "wapi": "where",
    "interpreter": "interpreter",
    "need interpreter": "interpreter",
    "need help": "need_help",
    "cant go": "cant_go",
    "can't go": "cant_go",
}
BARRIERS = {"fear", "cost", "transport", "stigma", "where"}
_active_db: Session | None = None
_active_enrolment: Enrolment | None = None
READY_REPLIES = [
    {"id": "been", "label": "I have been"},
    {"id": "not_yet", "label": "Not yet"},
    {"id": "worse", "label": "I feel worse"},
    {"id": "transport", "label": "Transport"},
    {"id": "fear", "label": "Fear"},
]


def guide_speaks(reply_text: str) -> str:
    """The guide says the core reply and nothing else."""
    return reply_text


def ussd_contract(reply_text: str, end: bool = False) -> dict:
    return {"text": reply_text[:182], "continue_session": not end}


def get_session(db: Session, channel: str, session_key: str) -> ChannelSession:
    row = db.scalar(
        select(ChannelSession).where(
            ChannelSession.channel == channel,
            ChannelSession.session_key == session_key,
        )
    )
    if row:
        return row
    row = ChannelSession(
        channel=channel,
        session_key=session_key,
        step="language",
        language="en",
        updated_at=clock.now(),
    )
    db.add(row)
    db.flush()
    return row


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s']", " ", (text or "").lower())).strip()


def classify(text: str) -> str | None:
    low = _norm(text)
    if not low:
        return None
    for label in ("danger", "distress", "diagnosis", "skip"):
        for phrase in lexicon().get(label, []):
            if phrase in low:
                return label
    return None


def _enrolment(db: Session, public_id: str | None) -> Enrolment | None:
    if not public_id:
        return None
    return db.scalar(select(Enrolment).where(Enrolment.public_id == public_id))


def _audit(db, enrolment: Enrolment | None, label: str, channel: str, escalation: str | None):
    audit.record(
        db,
        actor=None,
        action="conversation.turn",
        entity_type="followup",
        entity_id=enrolment.id if enrolment else None,
        patient_id=enrolment.patient_id if enrolment else None,
        detail={"label": label, "channel": channel, "escalation": escalation or ""},
    )


def _task(db, enrolment: Enrolment | None, task_type: str, priority: str):
    if enrolment is None or enrolment.case_id is None:
        return None
    return create_task(
        db,
        task_type=task_type,
        priority=priority,
        case_id=enrolment.case_id,
        source="followup",
    )


def _with_db(fn):
    @wraps(fn)
    def wrapped(db: Session, *args, **kwargs):
        global _active_db
        previous = _active_db
        _active_db = db
        try:
            return fn(db, *args, **kwargs)
        finally:
            _active_db = previous

    return wrapped


def _attach(result: dict, channel: str, language: str) -> dict:
    db = _active_db
    if db is None:
        result["ksl"] = {
            "available": False,
            "fallback": "captions",
            "caption": result["reply_text"],
        }
        return result
    from app.modules.ksl.registry import for_channel

    result["ksl"] = for_channel(db, result["template_id"], result["reply_text"], channel)
    if language == "ksl" and channel == "telegram" and not result["ksl"].get("available"):
        _task(db, _active_enrolment, "followup_ksl", "high")
    return result


def _pack(reply_key: str, language: str, channel: str, escalation: str | None, actions: list):
    replies = (
        READY_REPLIES if reply_key in {"status", "not_yet", "same", "better", "start_ack"} else []
    )
    if reply_key == "ask_language":
        replies = [
            {"id": "en", "label": "English"},
            {"id": "sw", "label": "Kiswahili"},
            {"id": "ksl", "label": "American Sign Language"},
        ]
    result = {
        "reply_text": fit(line(reply_key, language), channel),
        "quick_replies": replies,
        "actions": actions,
        "escalation_label": escalation,
        "template_id": reply_key,
    }
    return _attach(result, channel, language)


def log_outbound(db, public_id, channel, purpose, mode, body):
    db.add(
        Outbound(
            public_id=public_id,
            channel=channel,
            purpose_label=purpose,
            mode_label=mode,
            body=body,
            created_at=clock.now(),
        )
    )


@_with_db
def respond(db: Session, enrolment: Enrolment, channel: str, language: str, message: str) -> dict:
    """Safety, then a fixed menu. Web may add one approved line. No generation."""
    global _active_enrolment
    _active_enrolment = enrolment
    if language == "ksl":
        enrolment.language = "ksl"
    enrolment.window_open_until = clock.now() + timedelta(hours=24)
    text = (message or "").strip()
    if text:
        enrolment.missed_replies = 0
    low = _norm(text)
    label = classify(text)

    if enrolment.messages_stopped and low not in {"start", "anza"}:
        result = _pack("stop_ack", language, channel, None, [])
        _audit(db, enrolment, "stopped", channel, None)
        return result

    if low in {"stop", "simama"}:
        enrolment.messages_stopped = True
        result = _pack("stop_ack", language, channel, None, ["stop"])
        _audit(db, enrolment, "stop", channel, None)
        return result
    if low in {"start", "anza"}:
        enrolment.messages_stopped = False
        result = _pack("start_ack", language, channel, None, ["start"])
        _audit(db, enrolment, "start", channel, None)
        return result

    if label in {"danger", "distress"}:
        _task(db, enrolment, "followup_urgent", "urgent")
        if label == "danger":
            enrolment.symptom_flag = "worse"
        escalation = "danger_sign" if label == "danger" else "distress"
        result = _pack("danger", language, channel, escalation, ["open_task"])
        _audit(db, enrolment, label, channel, escalation)
        return result

    if label == "diagnosis":
        _task(db, enrolment, "followup_review", "high")
        result = _pack("refuse_diagnosis", language, channel, "diagnosis_request", ["open_task"])
        _audit(db, enrolment, "diagnosis_request", channel, "diagnosis_request")
        return result
    if label == "skip":
        _task(db, enrolment, "followup_review", "high")
        result = _pack("refuse_skip", language, channel, "skip_request", ["open_task"])
        _audit(db, enrolment, "skip_request", channel, "skip_request")
        return result

    choice = MENU.get(low)
    if choice == "been":
        enrolment.reported_visit = True
        result = _pack("been", language, channel, None, ["reported_visit"])
    elif choice == "not_yet":
        result = _pack("not_yet", language, channel, None, [])
    elif choice in {"same", "better"}:
        enrolment.symptom_flag = choice
        result = _pack(choice, language, channel, None, [f"symptom_{choice}"])
    elif choice == "worse":
        enrolment.symptom_flag = "worse"
        _task(db, enrolment, "followup_urgent", "urgent")
        result = _pack("worse", language, channel, "worse", ["open_task"])
    elif choice in BARRIERS:
        enrolment.barrier_label = choice
        _task(db, enrolment, "followup_barrier", "normal")
        result = _pack(choice, language, channel, None, ["barrier_confirmed"])
    elif choice == "interpreter":
        enrolment.barrier_label = "interpreter"
        _task(db, enrolment, "followup_barrier", "normal")
        result = _pack("interpreter", language, channel, None, ["barrier_confirmed"])
    elif choice in {"need_help", "cant_go"}:
        _task(db, enrolment, "followup_review", "high")
        result = _pack(choice, language, channel, "needs_person", ["open_task"])
    elif text == "":
        result = _pack("status", language, channel, None, [])
    else:
        _task(db, enrolment, "followup_review", "normal")
        result = _pack("unclear", language, channel, "unclear", ["open_task"])

    if channel == "web" and choice is None and text == "":
        result["reply_text"] = fit(
            line("status", language) + " " + line("slip_3", language), channel
        )
    _audit(
        db,
        enrolment,
        choice or ("unclear" if text else "status"),
        channel,
        result["escalation_label"],
    )
    return result


@_with_db
def handle(db: Session, session: ChannelSession, message: str) -> dict:
    """Opening flow, then the same core. Language, then ID, then the code, then status."""
    from app.modules.followup.access import code_ok, issue_code
    from app.modules.followup.ids import parse_public_id

    global _active_enrolment
    text = (message or "").strip()
    safety = classify(text)
    enrolment = _enrolment(db, session.public_id)
    _active_enrolment = enrolment
    low = _norm(text)
    if low in {"stop", "simama"}:
        if enrolment:
            enrolment.messages_stopped = True
        result = _pack("stop_ack", session.language, session.channel, None, ["stop"])
        _audit(db, enrolment, "stop", session.channel, None)
        return result
    if low in {"start", "anza"} and enrolment:
        enrolment.messages_stopped = False
        return respond(db, enrolment, session.channel, session.language, text)
    if safety in {"danger", "distress"}:
        if enrolment:
            return respond(db, enrolment, session.channel, session.language, text)
        result = _pack("danger", session.language, session.channel, "danger_sign", [])
        _audit(db, None, safety, session.channel, "danger_sign")
        return result

    if session.step == "language":
        low = text.lower()
        if low in {"1", "en", "english"}:
            session.language = "en"
            session.step = "id"
            return _pack("ask_id", "en", session.channel, None, [])
        if low in {"2", "sw", "kiswahili", "swahili"}:
            session.language = "sw"
            session.step = "id"
            return _pack("ask_id", "sw", session.channel, None, [])
        if low in {"3", "ksl", "kenyan sign language"}:
            session.language = "ksl"
            session.step = "id"
            return _pack("ask_id", "ksl", session.channel, None, [])
        return _pack("ask_language", "en", session.channel, None, [])

    if session.step == "id":
        public_id = parse_public_id(text)
        found = _enrolment(db, public_id) if public_id else None
        if found is None:
            return _pack("id_rejected", session.language, session.channel, None, [])
        issue_code(db, found.public_id)
        session.public_id = found.public_id
        session.step = "code"
        return _pack("ask_code", session.language, session.channel, None, [])

    if session.step == "code":
        if not code_ok(db, session.public_id or "", text, session.session_key):
            session.public_id = None
            session.step = "id"
            return _pack("id_rejected", session.language, session.channel, None, [])
        session.step = "ready"
        enrolment = _enrolment(db, session.public_id)
        if enrolment is None:
            return _pack("id_rejected", session.language, session.channel, None, [])
        return respond(db, enrolment, session.channel, session.language, "")

    enrolment = _enrolment(db, session.public_id)
    if enrolment is None:
        session.step = "id"
        return _pack("ask_id", session.language, session.channel, None, [])
    case = db.get(CareCase, enrolment.case_id) if enrolment.case_id else None
    if case is None:
        return _pack("unclear", session.language, session.channel, "unclear", [])
    return respond(db, enrolment, session.channel, session.language, text)
