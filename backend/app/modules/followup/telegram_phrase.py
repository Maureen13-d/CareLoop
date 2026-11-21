"""Optional wording over an approved Telegram line.

The model may rephrase one packet. It may not add a fact. Danger, worse, and
the sign-in lines stay verbatim. With no API key, every line is unchanged.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

import httpx

from app.core.config import BACKEND_DIR

LOCKED = {
    "greeting",
    "privacy",
    "declined",
    "ask_id",
    "ask_code",
    "id_rejected",
    "start_verify",
    "token_bad",
    "stop_ack",
    "worse",
    "unsure",
    "danger",
    "refuse_diagnosis",
    "refuse_skip",
    "group_once",
}
ROUTE_KEYS = (
    "next_step",
    "visit_bring",
    "visit_time",
    "visit_someone",
    "visit_fees",
    "visit_scared",
    "help_fear",
    "help_cost",
    "help_transport",
    "help_where",
    "help_sign",
    "ask_person",
)
_BANNED = (
    "you are fine",
    "nothing to worry",
    "don't worry",
    "do not worry",
    "cancer",
    "diagnosis",
    "hiv",
    "positive",
    "screening",
    "result",
)
_NUMBER = re.compile(r"\d+")
_CLINIC = re.compile(r"Clinic:\s*([^,\n]+)", re.IGNORECASE)

_complete = None


def configured() -> bool:
    return bool(_setting("CARELOOP_LLM_API_KEY"))


def set_complete(fn) -> None:
    """Tests pass a fake completer. Production uses the HTTP client."""
    global _complete
    _complete = fn


def phrase_messages(messages: list[dict], language: str) -> list[dict]:
    if not configured():
        return messages
    for message in messages:
        key = str(message.get("template_id") or "")
        original = str(message.get("text") or "")
        if message.get("urgent") or key in LOCKED or not original.strip():
            continue
        rewritten = _rewrite(original, language)
        facts = [str(item) for item in message.get("facts") or []]
        if rewritten and _keeps_facts(rewritten, original, facts):
            message["text"] = rewritten
            message["phrased"] = True
    return messages


def route(question: str, options: dict[str, str]) -> str | None:
    """Return one offered key, or None. A key outside the offer is ignored."""
    if not configured() or not question.strip() or not options:
        return None
    catalogue = "\n".join(f"{key}: {_first_line(text)}" for key, text in options.items())
    system = (
        "Choose the one key that answers the question. "
        "Reply with that key and nothing else. If none fit, reply NONE."
    )
    user = f"Keys:\n{catalogue}\n\nQuestion:\n{question.strip()[:500]}"
    try:
        raw = _ask(system, user)
    except (httpx.HTTPError, KeyError, ValueError, TypeError):
        return None
    key = raw.strip().strip("`").split()[0].lower() if raw.strip() else ""
    if key == "none" or key not in options:
        return None
    return key


def _rewrite(original: str, language: str) -> str:
    system = (
        "Rewrite the approved line in plain words for the person. "
        "Use only facts that are already in the line. Add nothing. "
        "Do not say they are fine, do not name an illness, and do not give a result. "
        "Keep every number, the clinic name, and any PENDING CLINICAL REVIEW line. "
        "If you cannot, return the approved line unchanged."
    )
    user = f"Language: {language or 'en'}\nApproved:\n{original}"
    try:
        raw = _ask(system, user)
    except (httpx.HTTPError, KeyError, ValueError, TypeError):
        return ""
    return raw.strip().strip('"')


def _ask(system: str, user: str) -> str:
    if _complete is not None:
        return _complete(system, user)
    key = _setting("CARELOOP_LLM_API_KEY")
    base = _base_url(key)
    model = _model(base)
    headers = {"Authorization": f"Bearer {key}"}
    payload = {
        "model": model,
        "temperature": 0.3,
        "max_tokens": 180,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if "openrouter.ai" in base:
        headers["HTTP-Referer"] = "https://careloop-screening-api.fly.dev"
        headers["X-Title"] = "CareLoop"
        payload["reasoning"] = {"enabled": False}
    response = httpx.post(
        f"{base}/chat/completions",
        headers=headers,
        json=payload,
        timeout=20.0,
    )
    response.raise_for_status()
    body = response.json()
    content = body["choices"][0]["message"].get("content")
    return "" if not content else str(content)


@lru_cache(maxsize=1)
def _file_values() -> dict[str, str]:
    path = Path(BACKEND_DIR) / ".env"
    found: dict[str, str] = {}
    if not path.is_file():
        return found
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, _, raw = stripped.partition("=")
        found[name.strip()] = raw.strip().strip('"').strip("'")
    return found


def _setting(name: str) -> str:
    """Process env wins, including an empty value. The developer file fills a gap."""
    if name in os.environ:
        return os.environ[name].strip()
    return _file_values().get(name, "").strip()


def _base_url(key: str) -> str:
    chosen = _setting("CARELOOP_LLM_BASE_URL")
    if chosen:
        return chosen.rstrip("/")
    if key.startswith("sk-or-"):
        return "https://openrouter.ai/api/v1"
    return "https://api.openai.com/v1"


def _model(base: str) -> str:
    chosen = _setting("CARELOOP_LLM_MODEL")
    if chosen:
        return chosen
    if "openrouter.ai" in base:
        return "nvidia/nemotron-3-super-120b-a12b"
    return "gpt-4o-mini"


_ORDINARY = {
    "a",
    "an",
    "and",
    "any",
    "ask",
    "at",
    "between",
    "bring",
    "can",
    "clinic",
    "come",
    "for",
    "go",
    "have",
    "if",
    "issue",
    "it",
    "keep",
    "many",
    "or",
    "person",
    "please",
    "see",
    "still",
    "talk",
    "tell",
    "thanks",
    "that",
    "the",
    "this",
    "to",
    "visit",
    "with",
    "yes",
    "you",
    "your",
}


def _keeps_facts(rewritten: str, original: str, facts: list[str] | None = None) -> bool:
    if not rewritten or len(rewritten) > 600:
        return False
    low = rewritten.lower()
    source = original.lower()
    if any(phrase in low and phrase not in source for phrase in _BANNED):
        return False
    if any(number not in rewritten for number in _NUMBER.findall(original)):
        return False
    clinic = _CLINIC.search(original)
    if clinic and clinic.group(1).strip().lower() not in low:
        return False
    for fact in facts or []:
        if fact.strip() and fact.strip().lower() not in low:
            return False
    if _invented_place(low, source) or _invented_name(rewritten, source):
        return False
    missing_review = "pending clinical review" in source and "pending clinical review" not in low
    return not missing_review


def _invented_place(rewritten: str, original: str) -> bool:
    from app.modules.followup.telegram_copy import clinics

    for area in clinics().get("areas") or []:
        for place in area.get("clinics") or []:
            name = str(place.get("name") or "").strip().lower()
            if name and name in rewritten and name not in original:
                return True
    return False


def _invented_name(rewritten: str, original: str) -> bool:
    for word in re.findall(r"\b[A-Z][a-z]{2,}\b", rewritten):
        token = word.lower()
        if token in _ORDINARY or token in original:
            continue
        return True
    return False


def _first_line(text: str) -> str:
    return text.splitlines()[0][:140]
