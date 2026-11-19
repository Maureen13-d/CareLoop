"""The assistant: safety rules first, then Lite mode. Pure functions with no database or
network access, so USSD, SMS and web chat can all call it, and tests can run it quickly.

Later tiers (grounded retrieval, optional language model) will be added above Lite mode
and must fall back to it on any failure."""
from app.modules.assistant.lexicon import get_template, load_barriers
from app.modules.assistant.lite import confidence, match_lite
from app.modules.assistant.safety import check_safety
from app.modules.assistant.schemas import (
    AssistantRequest, AssistantResponse, BarrierFlag, SafetyResult, SuggestedTask,
)
from app.modules.assistant.text import normalise


def _respond(template_id: str, *, tier: str, intents=None, flags=None, safety=None, needs_human=False, task=None) -> AssistantResponse:
    tpl = get_template(template_id)
    return AssistantResponse(
        reply_text=tpl["text"],
        intents=intents or [],
        barrier_flags=flags or [],
        safety=safety or SafetyResult(),
        needs_human=needs_human,
        suggested_task=task,
        template_id=template_id,
        tier=tier,
        contains_placeholder=bool(tpl.get("placeholder")),
    )


def _handle_menu(req: AssistantRequest) -> AssistantResponse:
    flag = load_barriers().worry_menu.get(req.menu_choice or "")
    if not flag:
        return _respond("lite.clarify", tier="lite")
    return _respond(
        f"lite.barrier.{flag}", tier="lite",
        flags=[BarrierFlag(flag=flag, confidence=1.0, status="confirmed", source="menu")],
        task=SuggestedTask(type="navigator_followup", priority="normal"),
    )


def handle_message(req: AssistantRequest) -> AssistantResponse:
    if req.menu_choice and req.menu_context == "worry_menu":
        return _handle_menu(req)

    norm = normalise(req.text)
    safety = check_safety(norm)
    lite = match_lite(norm)
    lex = load_barriers()
    flags = [BarrierFlag(flag=f, confidence=confidence(s), status="suggested", source="keyword") for f, s in lite.flags]

    # Tier 0: safety. Order matters: crisis, then distress, then symptoms, then diagnosis requests.
    if safety.level == "crisis":
        return _respond("safety.crisis", tier="safety", intents=lite.intents, flags=flags, safety=safety, needs_human=True,
                        task=SuggestedTask(type="counsellor_urgent", priority="urgent"))
    if safety.level == "distress":
        return _respond("safety.distress", tier="safety", intents=lite.intents, flags=flags, safety=safety, needs_human=True,
                        task=SuggestedTask(type="counsellor_contact", priority="high"))
    if safety.level == "symptom_report":
        return _respond("safety.symptom", tier="safety", intents=lite.intents, flags=flags, safety=safety, needs_human=True,
                        task=SuggestedTask(type="navigator_followup", priority="high"))
    if safety.level == "diagnosis_request":
        return _respond("safety.no_diagnosis", tier="safety", intents=lite.intents, flags=flags, safety=safety)

    # Tier 1: Lite mode.
    if "opt_out" in lite.intents:
        return _respond("lite.opt_out", tier="lite", intents=lite.intents)
    if "request_human" in lite.intents:
        return _respond("lite.request_human", tier="lite", intents=lite.intents, flags=flags, needs_human=True,
                        task=SuggestedTask(type="navigator_callback", priority="normal"))
    if lite.flags:
        if lite.ambiguous:
            return _respond("lite.clarify", tier="lite", intents=lite.intents, flags=flags)
        return _respond(f"lite.barrier.{lite.flags[0][0]}", tier="lite", intents=lite.intents, flags=flags,
                        task=SuggestedTask(type="navigator_followup", priority="normal"))
    if "greeting" in lite.intents:
        return _respond("lite.greeting", tier="lite", intents=lite.intents)
    return _respond("lite.unclear", tier="fallback")
