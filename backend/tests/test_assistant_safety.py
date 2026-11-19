import pytest

from app.modules.assistant.schemas import AssistantRequest
from app.modules.assistant.service import handle_message


def ask(text, channel="sms"):
    return handle_message(AssistantRequest(text=text, channel=channel))


@pytest.mark.parametrize("text", [
    "I want to die",
    "i dont want to live anymore",
    "I have been thinking about suicide",
    "I will kill myself",
    "I just want to END IT ALL",
    "i cant go on",
])
def test_crisis_language_goes_to_a_human_with_an_urgent_task(text):
    r = ask(text)
    assert r.safety.level == "crisis"
    assert r.tier == "safety"
    assert r.needs_human is True
    assert r.suggested_task.priority == "urgent"
    assert r.suggested_task.type == "counsellor_urgent"


def test_crisis_is_not_cancelled_by_a_negation_word():
    assert ask("i dont want to be alive").safety.level == "crisis"


def test_crisis_beats_every_other_category():
    r = ask("do i have cancer, i want to die")
    assert r.safety.level == "crisis"
    assert "diagnosis_request" in r.safety.matched


@pytest.mark.parametrize("text", [
    "do i have cancer",
    "Is it cancer?",
    "what does my result mean",
    "what treatment should I take",
    "do i need surgery",
])
def test_diagnosis_requests_are_declined_and_pointed_to_a_visit(text):
    r = ask(text)
    assert r.safety.level == "diagnosis_request"
    assert r.template_id == "safety.no_diagnosis"
    assert "cannot tell you" in r.reply_text.lower()
    assert r.needs_human is False


@pytest.mark.parametrize("text", ["i cant cope", "I feel so alone, nobody to talk to", "am i going to die"])
def test_distress_goes_to_a_human(text):
    r = ask(text)
    assert r.safety.level in ("distress", "crisis")
    assert r.needs_human is True


def test_symptom_reports_get_generic_contact_advice_and_a_high_priority_task():
    r = ask("I have heavy bleeding")
    assert r.safety.level == "symptom_report"
    assert r.needs_human is True
    assert r.suggested_task.priority == "high"
    assert r.contains_placeholder is True      # the wording still needs clinician review


def test_crisis_reply_still_contains_the_helpline_placeholder_until_verified():
    r = ask("i want to die")
    assert r.contains_placeholder is True
    assert "[VERIFIED HELPLINE]" in r.reply_text


def test_response_never_echoes_the_patients_words():
    r = ask("my husband beats me and i want to die")
    dumped = r.model_dump_json().lower()
    assert "husband" not in dumped and "beats" not in dumped


def test_ordinary_text_is_not_flagged():
    assert ask("what time is the clinic open").safety.level == "none"
