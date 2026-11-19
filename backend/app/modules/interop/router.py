from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_roles
from app.core.errors import DomainError
from app.modules.auth.models import ROLE_CLINICIAN, ROLE_NAVIGATOR
from app.modules.interop import service
from app.modules.interop.client import hospital_client
from app.modules.pathways.service import get_case

router = APIRouter(prefix="/cases", tags=["interop"])
staff = require_roles(ROLE_NAVIGATOR, ROLE_CLINICIAN)


@router.get("/{case_id}/hospital")
def get_link(case_id: int, db: Session = Depends(get_db), _=Depends(staff)):
    link = service.link_for(db, get_case(db, case_id).id)
    if link is None:
        raise DomainError(404, "not_found", "No visit has been sent to the simulated clinic yet.")
    return service.view(link)


@router.post("/{case_id}/hospital/request")
def post_request(
    case_id: int,
    db: Session = Depends(get_db),
    user=Depends(staff),
    client=Depends(hospital_client),
):
    link = service.request_visit(db, get_case(db, case_id), user, client)
    return service.view(link)


@router.post("/{case_id}/hospital/sync")
def post_sync(
    case_id: int,
    db: Session = Depends(get_db),
    user=Depends(staff),
    client=Depends(hospital_client),
):
    link = service.sync_milestones(db, get_case(db, case_id), user, client)
    return service.view(link)


@router.post("/{case_id}/hospital/advance")
def post_advance(
    case_id: int,
    db: Session = Depends(get_db),
    user=Depends(staff),
    client=Depends(hospital_client),
):
    link = service.advance_clinic(db, get_case(db, case_id), user, client)
    return service.view(link)
