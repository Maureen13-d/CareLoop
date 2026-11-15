from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.schemas import UtcDatetime

Purpose = Literal["care_coordination", "sms_reminders", "data_sharing_between_facilities"]


class PatientCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=100, description="Synthetic name only")
    age_band: str = Field(pattern=r"^\d{2}-\d{2}$", examples=["30-34"])
    zone: str = "Demo Zone A"
    preferred_language: Literal["en", "sw"] = "en"


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_ref: str
    display_name: str
    age_band: str
    zone: str
    preferred_language: str
    is_synthetic: bool


class ConsentIn(BaseModel):
    purpose: Purpose
    granted: bool


class ConsentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    purpose: str
    granted: bool
    granted_at: UtcDatetime
    revoked_at: UtcDatetime | None
