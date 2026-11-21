"""Maternal companion. Safety, then a scripted check-in, then a draft passage.

No model. Replies are the approved templates. PENDING CLINICAL REVIEW.
"""

from functools import lru_cache
from pathlib import Path

import yaml

from app.core.config import settings
from app.modules.assistant.safety import check_safety
from app.modules.assistant.schemas import (
    AssistantRequest,
    AssistantResponse,
    SafetyResult,
    SuggestedTask,
)
from app.modules.assistant.text import normalise
from app.modules.maternal.retrieve import search_maternal
from app.modules.maternal.triage import BANNED_SMS, triage_maternal

CHECKIN = {
    "bleeding": {"yes": "heavy_bleeding"},
    "headache": {"severe": "headache_severe", "mild": "headache_only"},
    "vision": {"blurred": "vision_blurred"},
    "swelling": {"yes": "swelling_face_hands"},
    "pain": {"upper": "severe_abdominal_pain"},
    "movement": {"none": "no_fetal_movement", "less": "reduced_fetal_movement"},
    "fever": {"severe": "fever_severe_weakness", "yes": "fever"},
    "fluid": {"fever": "leaking_fluid_fever", "yes": "leaking_fluid"},
    "breathing": {"yes": "difficulty_breathing"},
}
MOOD = {"low": "distress", "unsafe": "crisis"}


@lru_cache(maxsize=1)
def load_signs() -> dict:
    path = Path(settings.ai_dir) / "lexicon" / "maternal_signs.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    signs = {
        name: tuple(normalise(phrase) for phrase in phrases)
        for name, phrases in data["signs"].items()
    }
    return {
        "signs": signs,
        "crisis": tuple(normalise(phrase) for phrase in data["crisis"]),
        "distress": tuple(normalise(phrase) for phrase in data["distress"]),
        "all_clear": tuple(normalise(phrase) for phrase in data["all_clear"]),
    }


@lru_cache(maxsize=1)
def load_templates() -> dict:
    path = Path(settings.ai_dir) / "templates" / "maternal.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def discreet(text: str) -> bool:
    folded = text.lower()
    if any(word in folded for word in BANNED_SMS):
        return False
    return text.isascii() and len(text) <= 160 and "\n" not in text


def match_signs(text: str) -> list[str]:
    norm = normalise(text)
    found = []
    for name, phrases in load_signs()["signs"].items():
        if any(phrase and phrase in norm for phrase in phrases):
            found.append(name)
    return found


def _contains(text: str, phrases: tuple[str, ...]) -> bool:
    norm = normalise(text)
    return any(phrase and phrase in norm for phrase in phrases)


def answers_to_signs(answers: dict) -> tuple[list[str], str | None]:
    signs: list[str] = []
    mood = None
    for key, value in answers.items():
        if key == "mood":
            mood = MOOD.get(str(value))
            continue
        sign = CHECKIN.get(key, {}).get(str(value))
        if sign:
            signs.append(sign)
    return signs, mood


def parse_check_line(text: str) -> dict[str, str] | None:
    raw = (text or "").strip()
    if not raw.lower().startswith("check"):
        return None
    answers: dict[str, str] = {}
    for part in raw.split()[1:]:
        if part.lower() == "sw":
            continue
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        answers[key.lower()] = value.lower()
    return answers


def _reply(
    kind: str,
    language: str,
    *,
    safety: str = "none",
    needs_human: bool = False,
    task: SuggestedTask | None = None,
    source_ids: list[str] | None = None,
    sources: list[str] | None = None,
    tier: str = "safety",
) -> AssistantResponse:
    templates = load_templates()
    lang = language if language in templates else "en"
    text = templates[lang][kind]
    return AssistantResponse(
        reply_text=text,
        safety=SafetyResult(level=safety, matched=[kind]),
        needs_human=needs_human,
        suggested_task=task,
        template_id=f"maternal.{kind}.{lang}",
        source_ids=source_ids or [],
        sources=sources or [],
        tier=tier,
        review_status="draft_pending_clinical_review",
    )


def _from_level(level: str, language: str) -> AssistantResponse:
    if level == "red":
        return _reply(
            "red",
            language,
            safety="symptom_report",
            needs_human=True,
            task=SuggestedTask(type="maternal_warning", priority="urgent"),
        )
    if level == "yellow":
        return _reply("yellow", language, safety="symptom_report")
    return _reply("green", language, tier="lite")


def _triage_reply(signs: list[str], language: str, prior: str | None) -> AssistantResponse:
    decision = triage_maternal({}, signs, {"prior_level": prior})
    return _from_level(decision["level"], language)


def handle_maternal(req: AssistantRequest) -> AssistantResponse:
    language = req.language or "en"
    if req.channel == "sms" and req.consent_sms is False:
        return _reply("messages_off", language, tier="lite")

    if req.menu_context == "maternal_confirm" and req.menu_choice == "1":
        return _reply(
            "confirm",
            language,
            needs_human=True,
            task=SuggestedTask(type="navigator_callback", priority="normal"),
            tier="lite",
        )
    if req.menu_context == "maternal_home":
        return _reply("unclear", language, tier="lite")

    if req.checkin is not None:
        signs, mood = answers_to_signs(req.checkin)
        return _from_answers(signs, mood, language, req.prior_level, req.checkin)

    parsed = parse_check_line(req.text or "")
    if parsed is not None:
        signs, mood = answers_to_signs(parsed)
        return _from_answers(signs, mood, language, req.prior_level, parsed)

    text = req.text or ""
    if not text.strip():
        return _reply("unclear", language, tier="fallback")

    safety = check_safety(normalise(text))
    if safety.level == "crisis" or _contains(text, load_signs()["crisis"]):
        return _reply(
            "crisis",
            language,
            safety="crisis",
            needs_human=True,
            task=SuggestedTask(type="counsellor_urgent", priority="urgent"),
        )
    signs = match_signs(text)
    if signs:
        red_first = triage_maternal({}, signs, {"prior_level": req.prior_level})
        if red_first["level"] == "red":
            return _from_level("red", language)
    if safety.level == "distress" or _contains(text, load_signs()["distress"]):
        return _reply(
            "distress",
            language,
            safety="distress",
            needs_human=True,
            task=SuggestedTask(type="counsellor_contact", priority="high"),
        )
    if signs:
        return _triage_reply(signs, language, req.prior_level)
    if safety.level == "diagnosis_request":
        return _reply("no_diagnosis", language)
    if _contains(text, load_signs()["all_clear"]):
        return _reply("green", language, tier="lite")
    if req.channel == "web":
        passage = search_maternal(text)
        if passage:
            citation = f"{passage['source_title']} {passage['source_url']}".strip()
            return AssistantResponse(
                reply_text=str(passage["text"]).strip(),
                source_ids=[passage["id"]],
                sources=[citation],
                template_id=f"kb.{passage['id']}",
                tier="retrieval",
                review_status=passage.get("review_status", "draft_pending_clinical_review"),
            )
    return _reply("unclear", language, tier="fallback")


def _from_answers(
    signs: list[str],
    mood: str | None,
    language: str,
    prior: str | None,
    answers: dict | None = None,
) -> AssistantResponse:
    answers = answers or {}
    if mood == "crisis":
        return _reply(
            "crisis",
            language,
            safety="crisis",
            needs_human=True,
            task=SuggestedTask(type="counsellor_urgent", priority="urgent"),
        )
    if signs:
        decision = triage_maternal({}, signs, {"prior_level": prior})
        if decision["level"] == "red":
            return _from_level("red", language)
    if mood == "distress":
        return _reply(
            "distress",
            language,
            safety="distress",
            needs_human=True,
            task=SuggestedTask(type="counsellor_contact", priority="high"),
        )
    if signs:
        return _triage_reply(signs, language, prior)
    if mood is None and not signs and answers.get("all_clear") == "yes":
        return _reply("green", language, tier="lite")
    return _reply("unclear", language, tier="fallback")
