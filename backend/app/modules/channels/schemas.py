from pydantic import BaseModel, Field

from app.core.schemas import UtcDatetime


class UssdIn(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    phone_ref: str = Field(min_length=3, max_length=20)
    text: str = Field(default="", max_length=182)


class UssdOut(BaseModel):
    text: str
    end_session: bool = False


class SmsIn(BaseModel):
    phone_ref: str = Field(min_length=3, max_length=20)
    text: str = Field(min_length=1, max_length=160)


class SmsOut(BaseModel):
    id: int
    phone_ref: str
    direction: str
    body: str
    status: str
    created_at: UtcDatetime
