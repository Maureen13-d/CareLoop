from typing import Literal

from pydantic import BaseModel, Field

Finding = Literal["concerning", "urgent", "not_concerning", "inadequate"]
Channel = Literal["telegram", "sms", "ussd", "web"]
Language = Literal["en", "sw"]
ScreeningCode = Literal["cervical", "blood_pressure", "hiv", "tb", "general"]


class RegisterIn(BaseModel):
    age_band: str = Field(pattern=r"^\d{2}-\d{2}$")
    area_label: str = Field(min_length=1, max_length=40)
    screening_type: ScreeningCode
    finding: Finding
    consent: bool
    language: Language = "en"
    channel: Channel = "web"
    contact: str = ""
    assigned_chw_username: str | None = None


class CheckIn(BaseModel):
    public_id: str
    code: str = ""
    client_key: str = ""


class TalkIn(BaseModel):
    language: Language = "en"
    message: str = ""
    channel: Channel = "web"


class OutcomeIn(BaseModel):
    label: Literal["reached", "not_home", "barrier_noted"]


class TelegramIn(BaseModel):
    update_id: str | None = None
    chat_id: str
    text: str = ""
