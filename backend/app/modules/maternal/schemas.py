from pydantic import BaseModel


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
