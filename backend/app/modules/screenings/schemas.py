from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.core.schemas import UtcDatetime

ScreeningType = Literal["HPV_DNA", "VIA", "CYTOLOGY"]
ScreeningResult = Literal["negative", "positive", "inadequate", "suspected_cancer"]


class ScreeningIn(BaseModel):
    screening_type: ScreeningType
    result: ScreeningResult
    performed_at: datetime | None = None  # defaults to the (demo) current time


class ScreeningOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    screening_type: str
    result: str
    performed_at: UtcDatetime


class ScreeningRecorded(BaseModel):
    screening: ScreeningOut
    case_id: int | None
    case_status: Literal["opened", "already_open", "no_consent", "not_required"]
    message: str
