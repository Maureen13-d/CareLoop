"""The assistant: safety rules first, then Lite mode. Pure functions with no database or
network access, so USSD, SMS and web chat can all call it, and tests can run it quickly.

Web chat may quote one approved passage after Lite mode. SMS and USSD stay on the
short templates. An optional language model is not part of this build."""

from app.modules.assistant.lexicon import get_template, load_barriers
from app.modules.assistant.lite import confidence, match_lite
from app.modules.assistant.retrieve import search_passages
from app.modules.assistant.safety import check_safety
from app.modules.assistant.schemas import (
    AssistantRequest,
    AssistantResponse,
    BarrierFlag,
    SafetyResult,
    SuggestedTask,
)
from app.modules.assistant.text import normalise


def _respond(
    template_id: str,
    *,
    tier: str,
    intents=None,
    flags=None,
    safety=None,
    needs_human=False,
    task=None,
) -> AssistantResponse:
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
        f"lite.barrier.{flag}",
        tier="lite",
        flags=[BarrierFlag(flag=flag, confidence=1.0, status="confirmed", source="menu")],
        task=SuggestedTask(type="navigator_followup", priority="normal"),
    )


def _handle_confirm(req: AssistantRequest) -> AssistantResponse:
    flag = req.confirm_flag or ""
    if flag not in load_barriers().flags:
        return _respond("lite.clarify", tier="lite")
    return _respond(
        f"lite.barrier.{flag}",
        tier="lite",
        flags=[BarrierFlag(flag=flag, confidence=1.0, status="confirmed", source="menu")],
        task=SuggestedTask(type="navigator_followup", priority="normal"),
    )


def _from_passage(passage: dict) -> AssistantResponse:
    citation = f"{passage['source_title']} {passage['source_url']}".strip()
    return AssistantResponse(
        reply_text=str(passage["text"]).strip(),
        source_ids=[passage["id"]],
        sources=[citation],
        template_id=f"kb.{passage['id']}",
        tier="retrieval",
        review_status=passage.get("review_status", "draft_pending_clinical_review"),
    )


def handle_message(req: AssistantRequest) -> AssistantResponse:
    maternal = req.pathway == "maternal" or req.checkin is not None
    maternal = maternal or (req.menu_context or "").startswith("maternal")
    if maternal:
        from app.modules.maternal.companion import handle_maternal

        return handle_maternal(req)
    if req.menu_choice and req.menu_context == "worry_menu":
        return _handle_menu(req)
    if req.confirm_flag and not (req.text and req.text.strip()):
        return _handle_confirm(req)

    norm = normalise(req.text)
    safety = check_safety(norm)
    lite = match_lite(norm)
    load_barriers()
    flags = [
        BarrierFlag(flag=f, confidence=confidence(s), status="suggested", source="keyword")
        for f, s in lite.flags
    ]

    # Tier 0: safety. Order matters: crisis, then distress, then symptoms, then diagnosis requests.
    if safety.level == "crisis":
        return _respond(
            "safety.crisis",
            tier="safety",
            intents=lite.intents,
            flags=flags,
            safety=safety,
            needs_human=True,
            task=SuggestedTask(type="counsellor_urgent", priority="urgent"),
        )
    if safety.level == "distress":
        return _respond(
            "safety.distress",
            tier="safety",
            intents=lite.intents,
            flags=flags,
            safety=safety,
            needs_human=True,
            task=SuggestedTask(type="counsellor_contact", priority="high"),
        )
    if safety.level == "symptom_report":
        return _respond(
            "safety.symptom",
            tier="safety",
            intents=lite.intents,
            flags=flags,
            safety=safety,
            needs_human=True,
            task=SuggestedTask(type="navigator_followup", priority="high"),
        )
    if safety.level == "diagnosis_request":
        return _respond(
            "safety.no_diagnosis", tier="safety", intents=lite.intents, flags=flags, safety=safety
        )

    # Tier 1: Lite mode.
    if "opt_out" in lite.intents:
        return _respond("lite.opt_out", tier="lite", intents=lite.intents)
    if "request_human" in lite.intents:
        return _respond(
            "lite.request_human",
            tier="lite",
            intents=lite.intents,
            flags=flags,
            needs_human=True,
            task=SuggestedTask(type="navigator_callback", priority="normal"),
        )
    if lite.flags:
        if lite.ambiguous:
            return _respond("lite.clarify", tier="lite", intents=lite.intents, flags=flags)
        return _respond(
            f"lite.barrier.{lite.flags[0][0]}",
            tier="lite",
            intents=lite.intents,
            flags=flags,
            task=SuggestedTask(type="navigator_followup", priority="normal"),
        )
    if "greeting" in lite.intents:
        return _respond("lite.greeting", tier="lite", intents=lite.intents)
    # Web chat may quote an approved passage. SMS and USSD stay on the short templates.
    if req.channel == "web" and req.text:
        passage = search_passages(req.text)
        if passage:
            return _from_passage(passage)
    return _respond("lite.unclear", tier="fallback")
