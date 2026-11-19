"""The assistant contract: what goes in and what comes out. Channels (web, USSD, SMS)
and the navigation module code against these shapes."""
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Channel = Literal["web", "ussd", "sms"]
SafetyLevel = Literal["none", "diagnosis_request", "symptom_report", "distress", "crisis"]


class AssistantRequest(BaseModel):
    channel: Channel = "web"
    text: str | None = Field(default=None, max_length=1000)
    menu_choice: str | None = Field(default=None, max_length=2)
    menu_context: Literal["worry_menu"] | None = None   # which menu the choice answers
    language: Literal["en"] = "en"
    case_state: str | None = None                        # optional context from the pathway

    @model_validator(mode="after")
    def need_text_or_choice(self):
        if not (self.text and self.text.strip()) and not self.menu_choice:
            raise ValueError("Provide text or menu_choice")
        return self


class BarrierFlag(BaseModel):
    flag: str
    confidence: float
    status: Literal["suggested", "confirmed"]    # keyword matches stay "suggested" until the patient confirms
    source: Literal["keyword", "menu"]


class SafetyResult(BaseModel):
    level: SafetyLevel = "none"
    matched: list[str] = []                      # category names only; never the patient's words


class SuggestedTask(BaseModel):
    type: str
    priority: Literal["normal", "high", "urgent"]


class AssistantResponse(BaseModel):
    reply_text: str
    intents: list[str] = []
    barrier_flags: list[BarrierFlag] = []
    safety: SafetyResult = SafetyResult()
    needs_human: bool = False
    suggested_task: SuggestedTask | None = None
    template_id: str
    source_ids: list[str] = []                   # knowledge-base passages used (empty in Lite mode)
    tier: Literal["safety", "lite", "fallback"]
    review_status: str = "draft"
    contains_placeholder: bool = False           # True if the reply still holds text that must be verified
