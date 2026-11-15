from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_roles
from app.modules.auth.models import ROLE_CLINICIAN
from app.modules.patients import service as patients
from app.modules.screenings import service
from app.modules.screenings.schemas import ScreeningIn, ScreeningRecorded

router = APIRouter(prefix="/patients", tags=["screenings"])


@router.post("/{patient_id}/screenings", response_model=ScreeningRecorded, status_code=201)
def post_screening(patient_id: int, data: ScreeningIn, db: Session = Depends(get_db), user=Depends(require_roles(ROLE_CLINICIAN))):
    patient = patients.get_patient(db, patient_id)
    screening, case, status, message = service.record_screening(db, user, patient, data)
    return ScreeningRecorded(screening=screening, case_id=case.id if case else None, case_status=status, message=message)
