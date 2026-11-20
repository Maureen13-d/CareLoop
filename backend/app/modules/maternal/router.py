from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_roles
from app.modules.auth.models import ROLE_ADMIN, ROLE_CHW, ROLE_CLINICIAN, ROLE_NAVIGATOR
from app.modules.maternal import service
from app.modules.maternal.schemas import PregnancyOut

router = APIRouter(prefix="/maternal", tags=["maternal"])
readers = require_roles(ROLE_CHW, ROLE_NAVIGATOR, ROLE_CLINICIAN, ROLE_ADMIN)


@router.get("/pregnancies", response_model=list[PregnancyOut])
def pregnancies(db: Session = Depends(get_db), user=Depends(readers)):
    return service.list_pregnancies(db, user)
