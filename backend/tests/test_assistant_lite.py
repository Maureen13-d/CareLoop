import pytest

from app.modules.assistant.schemas import AssistantRequest
from app.modules.assistant.service import handle_message


def ask(text=None, channel="sms", **kw):
    return handle_message(AssistantRequest(text=text, channel=channel, **kw))


def flags(r):
    return [f.flag for f in r.barrier_flags]


@pytest.mark.parametrize("text, expected", [
    ("will it hurt", "fear_of_procedure_pain"),
    ("how much will it cost", "cost"),
    ("I have no money for this", "cost"),
    ("it is too far from the hospital", "transport_access"),
    ("I dont want anyone to know", "stigma_privacy"),
    ("where do i go", "no_info_where_to_go"),
    ("my husband refuses", "lack_of_support"),
    ("people say it is a death sentence", "misconception"),
    ("I am scared of bad news", "fear_of_diagnosis"),
])
def test_single_barrier_is_detected_as_a_suggestion(text, expected):
    r = ask(text)
    assert flags(r)[0] == expected
    assert r.barrier_flags[0].status == "suggested"      # not confirmed until the patient says so
    assert r.barrier_flags[0].source == "keyword"
    assert r.template_id == f"lite.barrier.{expected}"
    assert r.suggested_task.type == "navigator_followup"
    assert r.tier == "lite"


def test_negation_cancels_a_keyword_match():
    assert flags(ask("i am not afraid of the result")) == []
    assert flags(ask("i am not worried about cost")) == []


def test_two_close_barriers_trigger_a_clarifying_menu_and_keep_both_flags():
    r = ask("i cannot afford the transport and it is too far")
    assert r.template_id == "lite.clarify"
    assert set(flags(r)) >= {"cost", "transport_access"}


def test_sms_shorthand_is_understood():
    r = ask("pls call me")
    assert "request_human" in r.intents and r.needs_human is True
    assert r.suggested_task.type == "navigator_callback"


def test_exact_keywords_only_match_the_whole_message():
    assert "request_human" in ask("HELP").intents
    assert "request_human" not in ask("can you help me understand the clinic hours").intents


def test_opt_out_is_recognised_so_the_channel_can_revoke_consent():
    r = ask("STOP")
    assert "opt_out" in r.intents
    assert r.template_id == "lite.opt_out"


def test_greeting_and_unknown_text():
    assert ask("hello").template_id == "lite.greeting"
    r = ask("the weather is lovely today")
    assert r.template_id == "lite.unclear" and r.tier == "fallback" and r.needs_human is False


@pytest.mark.parametrize("choice, expected", [("1", "fear_of_procedure_pain"), ("2", "cost"), ("3", "transport_access"),
                                              ("4", "stigma_privacy"), ("5", "misconception")])
def test_menu_choice_gives_a_confirmed_flag(choice, expected):
    r = ask(menu_choice=choice, menu_context="worry_menu", channel="ussd")
    assert flags(r) == [expected]
    assert r.barrier_flags[0].status == "confirmed" and r.barrier_flags[0].source == "menu"
    assert r.barrier_flags[0].confidence == 1.0


def test_invalid_menu_choice_repeats_the_menu():
    assert ask(menu_choice="9", menu_context="worry_menu", channel="ussd").template_id == "lite.clarify"


def test_request_needs_text_or_a_menu_choice():
    with pytest.raises(ValueError):
        AssistantRequest(channel="sms")


def test_same_message_always_gives_the_same_answer():
    first = ask("how much will it cost to get checked").model_dump()
    assert all(ask("how much will it cost to get checked").model_dump() == first for _ in range(5))
