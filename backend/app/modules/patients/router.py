from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_roles
from app.modules.audit import service as audit
from app.modules.auth.models import ROLE_CLINICIAN, ROLE_NAVIGATOR
from app.modules.patients import service
from app.modules.patients.models import Patient
from app.modules.patients.schemas import ConsentIn, ConsentOut, PatientCreate, PatientOut

router = APIRouter(prefix="/patients", tags=["patients"])
staff = require_roles(ROLE_NAVIGATOR, ROLE_CLINICIAN)


@router.get("", response_model=list[PatientOut])
def list_patients(limit: int = Query(25, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db), _=Depends(staff)):
    return db.scalars(select(Patient).order_by(Patient.id).limit(limit).offset(offset)).all()


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db), user=Depends(staff)):
    patient = service.get_patient(db, patient_id)
    audit.record(db, actor=user, action="patient.view", entity_type="patient", entity_id=patient.id, patient_id=patient.id)
    db.commit()
    return patient


@router.post("", response_model=PatientOut, status_code=201)
def create_patient(data: PatientCreate, db: Session = Depends(get_db), user=Depends(staff)):
    return service.create_patient(db, user, data)


@router.post("/{patient_id}/consents", response_model=ConsentOut, status_code=201)
def post_consent(patient_id: int, data: ConsentIn, db: Session = Depends(get_db), user=Depends(staff)):
    patient = service.get_patient(db, patient_id)
    return service.record_consent(db, user, patient, data)
