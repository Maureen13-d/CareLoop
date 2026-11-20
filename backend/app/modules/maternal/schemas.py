from pydantic import BaseModel, Field


class PregnancyOut(BaseModel):
    id: int
    patient_ref: str
    display_name: str
    gestation_band: str
    area_label: str
    case_id: int | None
    case_state: str | None
    urgency: str | None
    risk_level: str | None


class ReadingIn(BaseModel):
    systolic: int | None = None
    diastolic: int | None = None
    pulse: int | None = None
    urine_protein: str | None = None
    hb_band: str | None = None
    danger_signs: list[str] = Field(default_factory=list)


class CheckInIn(BaseModel):
    channel: str = "web"
    language: str = "en"
    answers: dict[str, str]


class BarrierIn(BaseModel):
    flag: str


class VoucherIn(BaseModel):
    action: str


class CoverIn(BaseModel):
    status: str


class BandIn(BaseModel):
    device_id: str
    action: str
