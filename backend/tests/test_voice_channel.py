"""Voice simulator: seeded suggestive symptoms, same follow-up, no live call."""

import base64
import json

import pytest

from app.modules.followup import msingi
from app.modules.followup.models import ContactVault, Enrolment


@pytest.fixture(autouse=True)
def _spoken(monkeypatch):
    monkeypatch.setattr(msingi, "configured", lambda: True)
    monkeypatch.setattr(msingi, "speak", lambda _text: b"RIFF")
    monkeypatch.setattr(msingi, "hear", lambda *_args, **_kwargs: "worse")


def _cases(client, auth):
    response = client.get("/api/v1/followup/voice/cases", headers=auth["clin"])
    assert response.status_code == 200, response.text
    return response.json()["cases"]


def test_the_patient_card_speaks_only_the_approved_line(client, auth, monkeypatch):
    from tests.test_followup_loop import enrol, unlock

    said = []

    def speak(text):
        said.append(text)
        return b"RIFF"

    monkeypatch.setattr(msingi, "configured", lambda: True)
    monkeypatch.setattr(msingi, "speak", speak)
    opened = enrol(client, auth, channel="web")
    headers = unlock(client, auth, opened["public_id"])
    quiet = client.post(
        "/api/v1/followup/talk",
        json={"message": "not yet", "speak": False},
        headers=headers,
    )
    assert quiet.status_code == 200, quiet.text
    assert "audio_base64" not in quiet.json()
    aloud = client.post(
        "/api/v1/followup/talk",
        json={"message": "not yet", "speak": True},
        headers=headers,
    )
    assert aloud.status_code == 200, aloud.text
    assert aloud.json()["audio_base64"]
    assert said[-1] == aloud.json()["spoken_text"]
    assert "you are fine" not in said[-1].lower()


def test_a_patient_recording_is_transcribed_then_answered(client, auth):
    from tests.test_followup_loop import enrol, unlock

    opened = enrol(client, auth, channel="web")
    headers = unlock(client, auth, opened["public_id"])
    heard = client.post(
        "/api/v1/followup/hear",
        files={"file": ("turn.wav", b"RIFF", "audio/wav")},
        data={"language": "en"},
        headers=headers,
    )
    assert heard.status_code == 200, heard.text
    body = heard.json()
    assert body["heard_text"] == "worse"
    assert body["audio_base64"]
    assert "nearest clinic" in body["reply_text"].lower()


def test_voice_cases_seed_suggestive_symptoms_once(client, auth, db_session):
    first = _cases(client, auth)
    assert len(first) == 7
    assert all(item["symptom"] and item["say"] for item in first)
    keys = {item["key"] for item in first}
    assert keys == {"bleeding", "not-yet", "fare", "worse", "fear", "damu", "bado"}
    blob = json.dumps(first)
    assert "voice:" not in blob
    assert "07" not in blob
    second = _cases(client, auth)
    assert [item["public_id"] for item in second] == [item["public_id"] for item in first]
    stored = db_session.query(Enrolment).filter(Enrolment.channel == "voice").count()
    assert stored == 7
    contacts = db_session.query(ContactVault.contact_ref).all()
    assert all(not str(ref[0]).startswith("+") for ref in contacts if str(ref[0]).startswith("voice:"))


def test_opening_line_is_spoken_without_reply_codes(client, auth):
    case = next(item for item in _cases(client, auth) if item["key"] == "not-yet")
    response = client.post(
        "/api/v1/followup/voice/turn",
        json={"public_id": case["public_id"], "text": ""},
        headers=auth["clin"],
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["template_id"] == "status"
    assert "Reply" not in body["spoken_text"]
    assert "clinic" in body["spoken_text"].lower()
    assert base64.b64decode(body["audio_base64"]) == b"RIFF"
    assert body["synthetic"] is True


@pytest.mark.parametrize(
    ("key", "template_id"),
    [
        ("bleeding", "danger"),
        ("not-yet", "not_yet"),
        ("fare", "transport"),
        ("worse", "worse"),
        ("fear", "fear"),
        ("damu", "danger"),
        ("bado", "not_yet"),
    ],
)
def test_each_seeded_symptom_follows_the_same_core(client, auth, key, template_id):
    case = next(item for item in _cases(client, auth) if item["key"] == key)
    response = client.post(
        "/api/v1/followup/voice/turn",
        json={"public_id": case["public_id"], "text": case["say"]},
        headers=auth["clin"],
    )
    assert response.status_code == 200, response.text
    assert response.json()["template_id"] == template_id
    assert response.json()["heard_text"] == case["say"]


def test_recorded_audio_is_what_the_core_hears(client, auth, monkeypatch):
    monkeypatch.setattr(msingi, "hear", lambda content, filename, content_type: "worse")
    case = next(item for item in _cases(client, auth) if item["key"] == "worse")
    response = client.post(
        "/api/v1/followup/voice/hear",
        data={"public_id": case["public_id"]},
        files={"file": ("turn.wav", b"RIFFaudio", "audio/wav")},
        headers=auth["clin"],
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["heard_text"] == "worse"
    assert body["template_id"] == "worse"
    assert "clinic" in body["spoken_text"].lower()


def test_voice_check_in_requires_staff(client):
    response = client.get("/api/v1/followup/voice/cases")
    assert response.status_code == 401


def test_unknown_voice_id_is_refused(client, auth):
    _cases(client, auth)
    response = client.post(
        "/api/v1/followup/voice/turn",
        json={"public_id": "AAAA-BBBB-CCCC-D", "text": "worse"},
        headers=auth["clin"],
    )
    assert response.status_code == 404
