"""Maternal companion: discreet templates, check-ins, and the opt-in phone path."""

from app.modules.assistant.schemas import AssistantRequest
from app.modules.assistant.service import handle_message
from app.modules.maternal.companion import discreet, load_templates
from app.modules.maternal.retrieve import load_maternal_passages
from app.modules.maternal.triage import BANNED_SMS


def _ask(text, **kwargs):
    return handle_message(AssistantRequest(text=text, pathway="maternal", **kwargs))


def test_every_template_is_short_ascii_and_discreet():
    templates = load_templates()
    assert set(templates["en"]) == set(templates["sw"])
    for language in ("en", "sw"):
        for text in templates[language].values():
            assert discreet(text), text
            for word in BANNED_SMS:
                assert word not in text.lower()


def test_there_are_at_least_25_draft_passages_without_a_dose_or_a_banned_word():
    passages = load_maternal_passages()
    assert len(passages) >= 25
    for passage in passages:
        assert passage["review_status"] == "draft_pending_clinical_review"
        folded = passage["text"].lower()
        for word in BANNED_SMS:
            assert word not in folded
        assert "mg" not in folded


def test_bleeding_is_red_and_a_clean_line_is_not_green_by_default():
    red = _ask("heavy bleeding since morning")
    assert red.needs_human is True
    assert red.suggested_task is not None
    assert red.suggested_task.type == "maternal_warning"
    assert red.suggested_task.priority == "urgent"
    assert discreet(red.reply_text)
    unclear = _ask("hello there")
    assert unclear.template_id.endswith("unclear.en")
    assert unclear.needs_human is False


def test_swelling_asks_before_a_task_and_a_yes_opens_one():
    yellow = _ask("swelling of my face")
    assert yellow.needs_human is False
    assert yellow.suggested_task is None
    confirmed = handle_message(
        AssistantRequest(
            pathway="maternal",
            menu_context="maternal_confirm",
            menu_choice="1",
            channel="sms",
        )
    )
    assert confirmed.needs_human is True
    assert confirmed.suggested_task.type == "navigator_callback"


def test_headache_with_vision_and_a_prior_yellow_both_escalate():
    pair = handle_message(
        AssistantRequest(
            pathway="maternal",
            checkin={"headache": "severe", "vision": "blurred"},
        )
    )
    assert pair.template_id.startswith("maternal.red")
    escalated = handle_message(
        AssistantRequest(
            pathway="maternal",
            checkin={"headache": "mild"},
            prior_level="yellow",
        )
    )
    assert escalated.template_id.startswith("maternal.red")


def test_sms_without_consent_does_not_open_a_task():
    off = handle_message(
        AssistantRequest(
            pathway="maternal",
            channel="sms",
            text="heavy bleeding",
            consent_sms=False,
        )
    )
    assert off.template_id.startswith("maternal.messages_off")
    assert off.suggested_task is None


def test_swahili_reply_and_a_crisis_line():
    reply = _ask("damu nyingi", language="sw")
    assert reply.template_id.endswith(".sw")
    assert reply.needs_human is True
    crisis = _ask("nataka kufa")
    assert crisis.safety.level == "crisis"
    assert crisis.suggested_task.type == "counsellor_urgent"


def test_web_question_quotes_a_draft_passage_and_cervical_chat_does_not():
    maternal = _ask("what do the hub lights mean", channel="web")
    assert maternal.tier == "retrieval"
    assert maternal.source_ids == ["m_lights"]
    cervical = handle_message(AssistantRequest(channel="web", text="what do the hub lights mean"))
    assert cervical.source_ids != ["m_lights"]


def test_opt_in_ussd_checkin_stays_off_the_cervical_home(client):
    body = {"session_id": "m-1", "phone_ref": "+254700000777", "text": ""}
    home = client.post("/api/v1/channels/ussd", json=body)
    assert home.status_code == 200
    assert "1 Next step" in home.json()["text"]
    opened = client.post("/api/v1/channels/ussd", json={**body, "text": "M"})
    assert "Any bleeding?" in opened.json()["text"]
    assert len(opened.json()["text"]) <= 182
    steps = ["2", "3", "2", "2", "2", "3", "3", "3", "2", "3"]
    last = None
    for choice in steps:
        last = client.post("/api/v1/channels/ussd", json={**body, "text": choice})
        assert last.status_code == 200
        assert len(last.json()["text"]) <= 182
        folded = last.json()["text"].lower()
        for word in BANNED_SMS:
            assert word not in folded
    assert "usual day" in last.json()["text"]
