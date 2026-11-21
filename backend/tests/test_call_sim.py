"""Simulated handset call: same follow-up, spoken words, no phone network."""

import base64

import pytest

from app.modules.followup import msingi
from app.modules.followup import telegram_phrase as phrase


@pytest.fixture(autouse=True)
def _quiet(monkeypatch):
    monkeypatch.setattr(msingi, "configured", lambda: True)
    monkeypatch.setattr(msingi, "speak", lambda _text: b"RIFF")
    monkeypatch.setattr(phrase, "configured", lambda: False)


def _call(client, auth, session_id, text=""):
    response = client.post(
        "/api/v1/followup/call/simulate",
        json={"session_id": session_id, "text": text},
        headers=auth["clin"],
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "voice:" not in response.text
    assert "+254" not in response.text
    return body


def test_a_call_needs_a_signed_in_user(client):
    response = client.post(
        "/api/v1/followup/call/simulate",
        json={"session_id": "handset-1", "text": ""},
    )
    assert response.status_code == 401


def test_hello_asks_for_the_card_and_speaks_it(client, auth):
    body = _call(client, auth, "handset-hello", "Hello")
    assert body["simulated"] is True
    assert body["template_id"] == "call_open"
    assert "card" in body["spoken_text"].lower()
    assert body["audio_type"] == "audio/wav"
    assert base64.b64decode(body["audio_base64"]) == b"RIFF"
    labels = [item["label"] for item in body["phrases"]]
    assert "Hello" in labels
    assert any("-" in item["id"] for item in body["phrases"])


def test_hello_is_not_treated_as_an_id(client, auth):
    _call(client, auth, "handset-again", "")
    body = _call(client, auth, "handset-again", "Hello")
    assert body["template_id"] == "call_open"


def test_kiswahili_greets_in_kiswahili(client, auth):
    body = _call(client, auth, "handset-sw", "Kiswahili")
    assert body["template_id"] == "call_open"
    assert "Habari" in body["spoken_text"]


def test_saying_the_id_continues_the_check(client, auth):
    opened = _call(client, auth, "handset-id", "")
    example = next(item["id"] for item in opened["phrases"] if "-" in item["id"])
    body = _call(client, auth, "handset-id", example)
    assert body["template_id"] == "status"
    assert "clinic" in body["spoken_text"].lower()
    assert "Reply" not in body["spoken_text"]
    assert "Not yet" in [item["label"] for item in body["phrases"]]


def test_worse_on_the_call_still_sends_them_to_clinic(client, auth):
    opened = _call(client, auth, "handset-worse", "")
    example = next(item["id"] for item in opened["phrases"] if "-" in item["id"])
    _call(client, auth, "handset-worse", example)
    body = _call(client, auth, "handset-worse", "worse")
    assert body["template_id"] == "worse"
    assert "clinic" in body["spoken_text"].lower()
