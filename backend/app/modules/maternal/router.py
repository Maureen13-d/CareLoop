from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_roles
from app.modules.auth.models import (
    ROLE_ADMIN,
    ROLE_CHW,
    ROLE_CLINICIAN,
    ROLE_NAVIGATOR,
    ROLE_PROGRAM_MANAGER,
)
from app.modules.maternal import desk, devices, service
from app.modules.maternal.schemas import (
    BandIn,
    BarrierIn,
    CheckInIn,
    CoverIn,
    PregnancyOut,
    ReadingIn,
    VoucherIn,
)

router = APIRouter(prefix="/maternal", tags=["maternal"])
readers = require_roles(ROLE_CHW, ROLE_NAVIGATOR, ROLE_CLINICIAN, ROLE_ADMIN, ROLE_PROGRAM_MANAGER)
writers = require_roles(ROLE_CHW, ROLE_NAVIGATOR, ROLE_CLINICIAN)


@router.get("/pregnancies", response_model=list[PregnancyOut])
def pregnancies(db: Session = Depends(get_db), user=Depends(readers)):
    return service.list_pregnancies(db, user)


@router.get("/summary")
def maternal_summary(db: Session = Depends(get_db), user=Depends(readers)):
    return desk.summary(db, user)


@router.get("/cases/{case_id}")
def maternal_case(case_id: int, db: Session = Depends(get_db), user=Depends(readers)):
    return desk.case_bundle(db, user, case_id)


@router.post("/pregnancies/{pregnancy_id}/readings")
def manual_reading(
    pregnancy_id: int,
    data: ReadingIn,
    db: Session = Depends(get_db),
    user=Depends(writers),
):
    return desk.add_reading(db, user, pregnancy_id, data.model_dump())


@router.post("/pregnancies/{pregnancy_id}/checkins")
def checkin(
    pregnancy_id: int,
    data: CheckInIn,
    db: Session = Depends(get_db),
    user=Depends(writers),
):
    return desk.record_checkin(db, user, pregnancy_id, data.model_dump())


@router.post("/cases/{case_id}/barriers")
def barrier(case_id: int, data: BarrierIn, db: Session = Depends(get_db), user=Depends(writers)):
    return desk.add_barrier(db, user, case_id, data.flag)


@router.post("/cases/{case_id}/vouchers")
def voucher(case_id: int, data: VoucherIn, db: Session = Depends(get_db), user=Depends(writers)):
    return desk.set_voucher(db, user, case_id, data.action)


@router.post("/cases/{case_id}/cover")
def cover(case_id: int, data: CoverIn, db: Session = Depends(get_db), user=Depends(writers)):
    return desk.set_cover(db, user, case_id, data.status)


@router.post("/pregnancies/{pregnancy_id}/band")
def band(pregnancy_id: int, data: BandIn, db: Session = Depends(get_db), user=Depends(writers)):
    return desk.set_band(db, user, pregnancy_id, data.device_id, data.action)


@router.post("/devices/offline")
def offline(db: Session = Depends(get_db), user=Depends(writers)):
    return {"opened": devices.note_offline(db), "actor": user.role}


@router.post("/tasks/{task_id}/done")
def done_task(task_id: int, db: Session = Depends(get_db), user=Depends(writers)):
    return desk.finish_device_task(db, user, task_id)
