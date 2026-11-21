"""Voice follow-up in the simulator. Same core, spoken by Msingi. No phone network."""

import base64
from functools import lru_cache

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import REPO_ROOT
from app.core.errors import DomainError
from app.modules.auth.models import User
from app.modules.followup import msingi
from app.modules.followup.conversation import get_session, handle, log_outbound, respond
from app.modules.followup.ids import parse_public_id
from app.modules.followup.models import ContactVault, Enrolment
from app.modules.followup.register import register_followup
from app.modules.followup.schemas import RegisterIn
from app.modules.followup.telegram_phrase import phrase_line
from app.modules.followup.texts import line, spoken
from app.modules.patients.models import Patient

CASES = REPO_ROOT / "config" / "voice_cases.yaml"
MAX_AUDIO = 1_500_000
SEED_PREFIX = "voice:"


@lru_cache(maxsize=1)
def stories() -> tuple[dict, ...]:
    with open(CASES, encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    return tuple(loaded.get("cases") or ())


def _clinician(db: Session) -> User | None:
    return db.scalar(select(User).where(User.role == "clinician"))


def _chw_username(db: Session) -> str | None:
    chw = db.scalar(select(User).where(User.role == "chw"))
    return chw.username if chw else None


def ensure_voice_cases(db: Session) -> None:
    """Create the synthetic voice patients once. Safe to call again."""
    actor = _clinician(db)
    if actor is None:
        return
    chw = _chw_username(db)
    for story in stories():
        ref = f"{SEED_PREFIX}{story['key']}"
        existing = db.scalar(select(ContactVault).where(ContactVault.contact_ref == ref))
        if existing is not None:
            continue
        register_followup(
            db,
            actor,
            RegisterIn(
                age_band=story["age_band"],
                area_label=story["area_label"],
                screening_type=story["screening_type"],
                finding=story["finding"],
                consent=True,
                language=story["language"],
                channel="voice",
                contact=ref,
                assigned_chw_username=chw,
            ),
        )


def _script_for(contact_ref: str | None) -> dict:
    if not contact_ref or not contact_ref.startswith(SEED_PREFIX):
        return {}
    key = contact_ref.removeprefix(SEED_PREFIX)
    for story in stories():
        if story["key"] == key:
            return story
    return {}


def list_cases(db: Session) -> dict:
    ensure_voice_cases(db)
    rows = db.scalars(select(Enrolment).where(Enrolment.channel == "voice")).all()
    order = {story["key"]: index for index, story in enumerate(stories())}
    cases = []
    for enrolment in rows:
        vault = db.scalar(select(ContactVault).where(ContactVault.public_id == enrolment.public_id))
        script = _script_for(vault.contact_ref if vault else None)
        patient = db.get(Patient, enrolment.patient_id)
        cases.append(
            {
                "key": script.get("key") or enrolment.public_id,
                "public_id": enrolment.public_id,
                "language": enrolment.language,
                "area_label": enrolment.area_label,
                "age_band": patient.age_band if patient else "",
                "finding": enrolment.finding,
                "symptom": script.get("symptom") or "Voice follow-up.",
                "say": script.get("say") or "not yet",
            }
        )
    cases.sort(key=lambda item: order.get(item["key"], 100))
    return {"synthetic": True, "cases": cases}


def _enrolment(db: Session, public_id: str) -> Enrolment:
    canonical = parse_public_id(public_id)
    found = None
    if canonical:
        found = db.scalar(
            select(Enrolment).where(
                Enrolment.public_id == canonical,
                Enrolment.channel == "voice",
            )
        )
    if found is None:
        raise DomainError(404, "not_found", "That voice check-in is not available.")
    return found


def speak_reply(result: dict) -> dict:
    """Speak the approved line already chosen for this reply. Never a client sentence."""
    text = str(result.get("spoken_text") or result.get("reply_text") or "").strip()
    result["audio_base64"] = None
    result["audio_type"] = "audio/wav"
    result["audio_error"] = None
    if not text:
        return result
    if not msingi.configured():
        result["audio_error"] = "Voice is not configured."
        return result
    try:
        wav = msingi.speak(text)
    except msingi.MsingiError as exc:
        result["audio_error"] = str(exc)
        return result
    result["audio_base64"] = base64.b64encode(wav).decode("ascii")
    return result


def hear_patient(db: Session, enrolment: Enrolment, content: bytes, filename: str, content_type: str, language: str) -> dict:
    """Transcribe a patient's recording, then answer with the same guide as a typed turn."""
    if not content or len(content) > MAX_AUDIO:
        raise DomainError(422, "not_heard", "No speech was heard. Say it again.")
    try:
        heard = msingi.hear(content, filename, content_type)
    except msingi.MsingiError as exc:
        raise DomainError(502, "voice_unavailable", str(exc)) from exc
    if not heard:
        raise DomainError(422, "not_heard", "No speech was heard. Say it again.")
    chosen = language if language in {"en", "sw", "ksl"} else "en"
    result = respond(db, enrolment, "web", chosen, heard)
    result["spoken_text"] = result["reply_text"]
    result["heard_text"] = heard
    speak_reply(result)
    db.commit()
    return result


def turn(
    db: Session,
    public_id: str,
    text: str = "",
    audio: tuple[bytes, str, str] | None = None,
) -> dict:
    """One spoken turn. Audio is transcribed first. The core decides the reply."""
    ensure_voice_cases(db)
    enrolment = _enrolment(db, public_id)
    heard = (text or "").strip()
    if audio is not None:
        content, filename, content_type = audio
        if not content or len(content) > MAX_AUDIO:
            raise DomainError(422, "not_heard", "No speech was heard. Say it again.")
        try:
            heard = msingi.hear(content, filename, content_type)
        except msingi.MsingiError as exc:
            raise DomainError(502, "voice_unavailable", str(exc)) from exc
        if not heard:
            raise DomainError(422, "not_heard", "No speech was heard. Say it again.")

    result = respond(db, enrolment, "voice", enrolment.language, heard)
    spoken_text = spoken(result["template_id"], enrolment.language)
    log_outbound(db, enrolment.public_id, "voice", result["template_id"], "spoken", spoken_text)
    audio_b64 = None
    audio_error = None
    if msingi.configured():
        try:
            wav = msingi.speak(spoken_text)
            audio_b64 = base64.b64encode(wav).decode("ascii")
        except msingi.MsingiError as exc:
            audio_error = str(exc)
    else:
        audio_error = "Voice is not configured."
    db.commit()
    return {
        "synthetic": True,
        "public_id": enrolment.public_id,
        "heard_text": heard,
        "reply_text": result["reply_text"],
        "spoken_text": spoken_text,
        "template_id": result["template_id"],
        "escalation_label": result["escalation_label"],
        "audio_base64": audio_b64,
        "audio_type": "audio/wav",
        "audio_error": audio_error,
    }


_HELLOS = {"hello", "hi", "hey", "habari", "mambo"}
_SWAHILI = {"kiswahili", "swahili"}
_ENGLISH = {"english"}


def _example_id(db: Session) -> str | None:
    ensure_voice_cases(db)
    row = db.scalar(select(Enrolment.public_id).where(Enrolment.channel == "voice"))
    return row


def _call_phrases(db: Session, session) -> list[dict]:
    """Words the caller can say. The handset shows them; nothing is dialled."""
    if session.step == "id":
        phrases = [
            {"id": "Hello", "label": "Hello"},
            {"id": "English", "label": "English"},
            {"id": "Kiswahili", "label": "Kiswahili"},
        ]
        example = _example_id(db)
        if example:
            phrases.append({"id": example, "label": example})
        return phrases
    return [
        {"id": "not yet", "label": "Not yet"},
        {"id": "I have been", "label": "I have been"},
        {"id": "worse", "label": "I feel worse"},
    ]


def call_turn(db: Session, session_id: str, text: str = "") -> dict:
    """A simulated call. The core chooses the line, the model may soften it, Sauti speaks it."""
    session = get_session(db, "call", (session_id or "handset")[:80])
    if session.step == "language":
        session.language = "en"
        session.step = "id"
    heard = (text or "").strip()
    low = heard.lower()
    if session.step == "id" and low in _SWAHILI:
        session.language = "sw"
        heard = ""
    elif session.step == "id" and low in _ENGLISH:
        session.language = "en"
        heard = ""
    if not heard or (low in _HELLOS and session.step == "id"):
        template_id = "call_open"
        reply_text = line("call_open", session.language)
        spoken_text = spoken("call_open", session.language)
        escalation = None
    else:
        result = handle(db, session, heard)
        if result.get("template_id") == "ask_code" and session.public_id:
            found = db.scalar(select(Enrolment).where(Enrolment.public_id == session.public_id))
            if found is not None:
                session.step = "ready"
                result = respond(db, found, "call", session.language, "")
        template_id = result["template_id"]
        reply_text = result["reply_text"]
        spoken_text = spoken(template_id, session.language)
        escalation = result.get("escalation_label")
    spoken_text = phrase_line(spoken_text, template_id, session.language)
    log_outbound(db, session.public_id, "call", template_id, "spoken", spoken_text)
    payload = {
        "synthetic": True,
        "simulated": True,
        "heard_text": heard,
        "reply_text": reply_text,
        "spoken_text": spoken_text,
        "template_id": template_id,
        "escalation_label": escalation,
        "phrases": _call_phrases(db, session),
    }
    speak_reply(payload)
    db.commit()
    return payload
