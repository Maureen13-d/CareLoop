"""Msingi Sauti speech. This client speaks and transcribes. It does not dial."""

import httpx

from app.core.config import settings


class MsingiError(Exception):
    pass


def configured() -> bool:
    return bool(settings.msingi_api_key.strip())


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.msingi_api_key.strip()}"}


def _url(path: str) -> str:
    return settings.msingi_base_url.rstrip("/") + path


def _fail(response: httpx.Response) -> None:
    message = "Voice service could not complete that turn."
    try:
        body = response.json()
        nested = body.get("error") if isinstance(body, dict) else None
        if isinstance(nested, dict) and nested.get("message"):
            message = str(nested["message"])
        elif isinstance(body, dict) and body.get("error_msg"):
            message = str(body["error_msg"])
    except Exception:
        message = "Voice service could not complete that turn."
    raise MsingiError(message)


def speak(text: str) -> bytes:
    """Return WAV bytes for an approved line."""
    if not configured():
        raise MsingiError("Voice is not configured.")
    payload: dict[str, str] = {"text": text}
    voice = settings.msingi_voice.strip()
    if voice:
        payload["voice"] = voice
    try:
        response = httpx.post(_url("/v1/audio/speech"), json=payload, headers=_headers(), timeout=45)
        if response.status_code == 422 and "voice" in payload:
            payload.pop("voice")
            response = httpx.post(
                _url("/v1/audio/speech"), json=payload, headers=_headers(), timeout=45
            )
    except httpx.HTTPError as exc:
        raise MsingiError("Voice service could not be reached.") from exc
    if response.status_code >= 400:
        _fail(response)
    if not response.content:
        raise MsingiError("Voice service returned no audio.")
    return response.content


def hear(content: bytes, filename: str, content_type: str) -> str:
    """Transcribe one spoken turn. Returns the text Msingi heard."""
    if not configured():
        raise MsingiError("Voice is not configured.")
    try:
        response = httpx.post(
            _url("/v1/audio/transcriptions"),
            headers=_headers(),
            data={"model": "asr-general"},
            files={"file": (filename or "turn.wav", content, content_type or "audio/wav")},
            timeout=60,
        )
    except httpx.HTTPError as exc:
        raise MsingiError("Voice service could not be reached.") from exc
    if response.status_code >= 400:
        _fail(response)
    body = response.json()
    if not isinstance(body, dict):
        raise MsingiError("Voice service returned no words.")
    return str(body.get("text") or "").strip()
