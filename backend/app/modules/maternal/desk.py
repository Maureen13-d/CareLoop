"""Navigator and promoter actions for a maternal journey. Simulated money and cover."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.errors import DomainError
from app.modules.assistant.schemas import AssistantRequest
from app.modules.audit import service as audit
from app.modules.audit.models import AuditLog
from app.modules.auth.models import ROLE_CHW, ROLE_CLINICIAN, ROLE_NAVIGATOR, User
from app.modules.maternal.companion import CHECKIN, MOOD, handle_maternal, load_templates
from app.modules.maternal.devices import find_device, ingest_reading, lend_band, return_band
from app.modules.maternal.models import (
    Barrier,
    CheckIn,
    CoverCheck,
    Device,
    Pregnancy,
    Reading,
    Voucher,
)
from app.modules.maternal.service import assert_chw_assignment
from app.modules.pathways.loader import load_pathway
from app.modules.pathways.models import CareCase
from app.modules.patients.models import Patient
from app.modules.tasks.models import NavigatorTask
from app.modules.tasks.service import complete_task, create_task, should_open_task

BARRIERS = ("fare", "cover", "fear", "companion", "shared_phone")
VOUCHER_STATUS = {
    "request": "requested",
    "approve": "approved",
    "issue": "issued",
    "used": "used",
}
VOUCHER_ORDER = ("requested", "approved", "issued", "used")
COVER_STATUS = ("unknown", "assumed_covered", "assumed_not_covered")
DEVICE_TASKS = ("chw_cuff", "chw_battery", "device_offline")
CLINICAL = {ROLE_NAVIGATOR, ROLE_CLINICIAN}


def _pregnancy_for_case(db: Session, case: CareCase) -> Pregnancy:
    pregnancy = db.scalar(
        select(Pregnancy)
        .where(Pregnancy.patient_id == case.patient_id)
        .order_by(Pregnancy.id.desc())
    )
    if pregnancy is None:
        raise DomainError(404, "not_found", "No pregnancy is linked to this journey")
    return pregnancy


def _open_case(db: Session, pregnancy: Pregnancy) -> CareCase | None:
    return db.scalar(
        select(CareCase)
        .where(CareCase.patient_id == pregnancy.patient_id, CareCase.pathway_id == "maternal")
        .order_by(CareCase.id.desc())
    )


def _guard(db: Session, actor: User, case: CareCase) -> None:
    if case.pathway_id != "maternal":
        raise DomainError(409, "wrong_pathway", "That journey is not on the maternal pathway")
    if actor.role == ROLE_CHW:
        assert_chw_assignment(db, actor, case, "maternal.access")


def case_bundle(db: Session, actor: User, case_id: int) -> dict:
    case = db.get(CareCase, case_id)
    if case is None:
        raise DomainError(404, "not_found", "Journey not found")
    _guard(db, actor, case)
    pregnancy = _pregnancy_for_case(db, case)
    patient = db.get(Patient, case.patient_id)
    readings = db.scalars(
        select(Reading).where(Reading.pregnancy_id == pregnancy.id).order_by(Reading.taken_at)
    ).all()
    band = db.scalar(
        select(Device).where(
            Device.assigned_pregnancy_id == pregnancy.id,
            Device.kind == "band",
        )
    )
    return {
        "case_id": case.id,
        "state": case.state,
        "urgency": case.urgency,
        "patient_ref": patient.patient_ref if patient else "",
        "display_name": patient.display_name if patient else "",
        "gestation_band": pregnancy.gestation_band,
        "area_label": pregnancy.area_label,
        "consent_sms": pregnancy.consent_sms_reminders,
        "consent_band": pregnancy.consent_band_contact,
        "readings": [
            {
                "id": row.id,
                "taken_at": row.taken_at.isoformat(),
                "systolic": row.systolic,
                "diastolic": row.diastolic,
                "pulse": row.pulse,
                "urine_protein": row.urine_protein,
                "hb_band": row.hb_band,
                "danger_signs": row.danger_signs,
                "risk_level": row.risk_level,
                "source": row.source,
            }
            for row in readings
        ],
        "band": None
        if band is None
        else {
            "device_id": band.pseudonymous_device_id,
            "status": band.status,
            "battery_pct": band.battery_pct,
        },
        "barriers": [
            row.flag for row in db.scalars(select(Barrier).where(Barrier.case_id == case.id)).all()
        ],
        "vouchers": [
            {
                "id": row.id,
                "status": row.status,
                "amount_label": row.amount_label,
                "provider": row.simulated_provider,
            }
            for row in db.scalars(select(Voucher).where(Voucher.case_id == case.id)).all()
        ],
        "cover_checks": [
            {"id": row.id, "status": row.status, "source": row.source}
            for row in db.scalars(select(CoverCheck).where(CoverCheck.case_id == case.id)).all()
        ],
        "review": "PENDING CLINICAL REVIEW",
    }


def _hours_left(case: CareCase) -> float | None:
    if case.deadline_at is None:
        return None
    return round((case.deadline_at - clock.now()).total_seconds() / 3600, 1)


def _scoped_pregnancies(db: Session, actor: User) -> list[Pregnancy]:
    stmt = select(Pregnancy).order_by(Pregnancy.id)
    if actor.role == ROLE_CHW:
        stmt = stmt.where(Pregnancy.assigned_chw_id == actor.id)
    return list(db.scalars(stmt).all())


def summary(db: Session, actor: User) -> dict:
    pathway = load_pathway("maternal")
    pregnancies = _scoped_pregnancies(db, actor)
    patient_ids = {row.patient_id for row in pregnancies}
    cases = []
    if patient_ids:
        cases = list(
            db.scalars(
                select(CareCase).where(
                    CareCase.pathway_id == "maternal",
                    CareCase.patient_id.in_(patient_ids),
                )
            ).all()
        )
    open_cases = [case for case in cases if not pathway.is_terminal(case.state)]
    red_rows = []
    yellow = 0
    for case in open_cases:
        pregnancy = next((row for row in pregnancies if row.patient_id == case.patient_id), None)
        reading = None
        if pregnancy is not None:
            reading = db.scalar(
                select(Reading)
                .where(Reading.pregnancy_id == pregnancy.id)
                .order_by(Reading.id.desc())
            )
        level = reading.risk_level if reading else None
        if level == "red" or case.urgency == "urgent":
            patient = db.get(Patient, case.patient_id)
            red_rows.append(
                {
                    "case_id": case.id,
                    "patient_ref": patient.patient_ref if patient else "",
                    "display_name": patient.display_name if patient else "",
                    "hours_left": _hours_left(case),
                    "state": case.state,
                }
            )
        elif level == "yellow":
            yellow += 1
    red_rows.sort(key=lambda row: (row["hours_left"] is None, row["hours_left"] or 0))
    funnel = []
    for state in pathway.states:
        funnel.append(
            {
                "state": state,
                "label": pathway.states[state].label,
                "count": sum(1 for case in open_cases if case.state == state),
            }
        )
    since = clock.now() - timedelta(hours=24)
    sos = db.scalar(
        select(AuditLog.id).where(AuditLog.action == "band.sos", AuditLog.occurred_at >= since)
    )
    sos_count = len(
        db.scalars(
            select(AuditLog).where(AuditLog.action == "band.sos", AuditLog.occurred_at >= since)
        ).all()
    )
    tasks = db.scalars(
        select(NavigatorTask).where(
            NavigatorTask.status == "open",
            NavigatorTask.task_type.in_(DEVICE_TASKS),
        )
    ).all()
    return {
        "open": len(open_cases),
        "red": len(red_rows),
        "yellow": yellow,
        "unowned": sum(1 for case in open_cases if case.owner_user_id is None),
        "device_alerts": len(tasks),
        "sos_24h": sos_count,
        "funnel": funnel,
        "red_cases": red_rows,
        "device_tasks": [
            {"id": task.id, "title": task.title, "summary": task.summary, "priority": task.priority}
            for task in tasks
        ],
        "deadlines_status": pathway.deadlines_status,
        "review": "PENDING CLINICAL REVIEW",
        "sos_seen": sos is not None,
    }


def add_reading(db: Session, actor: User, pregnancy_id: int, body: dict) -> dict:
    pregnancy = db.get(Pregnancy, pregnancy_id)
    if pregnancy is None:
        raise DomainError(404, "not_found", "Pregnancy not found")
    case = _open_case(db, pregnancy)
    if case is not None and actor.role == ROLE_CHW:
        assert_chw_assignment(db, actor, case, "reading.manual")
    elif actor.role == ROLE_CHW and pregnancy.assigned_chw_id != actor.id:
        raise DomainError(403, "forbidden", "This person is not assigned to you")
    patient = db.get(Patient, pregnancy.patient_id)
    stamp = clock.now().strftime("%Y%m%d%H%M%S")
    return ingest_reading(
        db,
        device=None,
        pregnancy_ref=patient.patient_ref,
        client_reading_id=f"manual-{pregnancy.id}-{stamp}",
        systolic=body.get("systolic"),
        diastolic=body.get("diastolic"),
        pulse=body.get("pulse"),
        urine_protein=body.get("urine_protein"),
        hb_band=body.get("hb_band"),
        danger_signs=body.get("danger_signs") or [],
        hub_local_level=None,
        source="manual",
    )


def _clean_answers(answers: dict) -> dict[str, str]:
    clean: dict[str, str] = {}
    for key, value in answers.items():
        text = str(value)
        if (
            key == "mood"
            and text in MOOD
            or key == "all_clear"
            and text == "yes"
            or key in CHECKIN
            and text in CHECKIN[key]
        ):
            clean[key] = text
    return clean


def record_checkin(db: Session, actor: User, pregnancy_id: int, body: dict) -> dict:
    pregnancy = db.get(Pregnancy, pregnancy_id)
    if pregnancy is None:
        raise DomainError(404, "not_found", "Pregnancy not found")
    case = _open_case(db, pregnancy)
    if case is not None:
        _guard(db, actor, case)
    elif actor.role == ROLE_CHW and pregnancy.assigned_chw_id != actor.id:
        raise DomainError(403, "forbidden", "This person is not assigned to you")
    channel = body.get("channel") or "web"
    language = body.get("language") or "en"
    if channel == "sms" and not pregnancy.consent_sms_reminders:
        text = load_templates()["en" if language not in load_templates() else language][
            "messages_off"
        ]
        return {"stored": False, "reply": text, "task_id": None, "level": "off"}
    answers = _clean_answers(body.get("answers") or {})
    reading = db.scalar(
        select(Reading).where(Reading.pregnancy_id == pregnancy.id).order_by(Reading.id.desc())
    )
    prior = (
        reading.risk_level if reading and reading.risk_level in {"green", "yellow", "red"} else None
    )
    response = handle_maternal(
        AssistantRequest(
            channel=channel,
            pathway="maternal",
            language=language,
            checkin=answers,
            prior_level=prior,
            consent_sms=pregnancy.consent_sms_reminders or channel != "sms",
        )
    )
    level = "green"
    if response.template_id.startswith("maternal.red"):
        level = "red"
    elif response.template_id.startswith("maternal.yellow"):
        level = "yellow"
    elif response.template_id.startswith("maternal.crisis"):
        level = "crisis"
    elif response.template_id.startswith("maternal.distress"):
        level = "distress"
    db.add(
        CheckIn(
            pregnancy_id=pregnancy.id,
            channel=channel,
            answers=answers,
            risk_level=level,
            created_at=clock.now(),
        )
    )
    task_id = None
    if level == "red":
        from app.modules.maternal.devices import _flag_case

        patient = db.get(Patient, pregnancy.patient_id)
        case = _flag_case(db, patient, pregnancy, "red")
        task_id = db.scalar(
            select(NavigatorTask.id).where(
                NavigatorTask.case_id == case.id,
                NavigatorTask.task_type == "maternal_warning",
                NavigatorTask.status == "open",
            )
        )
    elif case is not None and should_open_task(response) and response.suggested_task:
        task = create_task(
            db,
            task_type=response.suggested_task.type,
            priority=response.suggested_task.priority,
            case_id=case.id,
            source="checkin",
            actor=actor,
        )
        task_id = task.id
    audit.record(
        db,
        actor=actor,
        action="checkin.recorded",
        entity_type="pregnancy",
        entity_id=pregnancy.id,
        patient_id=pregnancy.patient_id,
        detail={"level": level, "template_id": response.template_id, "channel": channel},
    )
    db.commit()
    return {
        "stored": True,
        "reply": response.reply_text,
        "task_id": task_id,
        "level": level,
        "template_id": response.template_id,
    }


def add_barrier(db: Session, actor: User, case_id: int, flag: str) -> dict:
    if flag not in BARRIERS:
        raise DomainError(422, "bad_flag", "That barrier is not one of the known labels")
    case = db.get(CareCase, case_id)
    if case is None:
        raise DomainError(404, "not_found", "Journey not found")
    _guard(db, actor, case)
    existing = db.scalar(select(Barrier).where(Barrier.case_id == case.id, Barrier.flag == flag))
    if existing is None:
        db.add(Barrier(case_id=case.id, flag=flag, created_at=clock.now()))
    audit.record(
        db,
        actor=actor,
        action="barrier.noted",
        entity_type="care_case",
        entity_id=case.id,
        patient_id=case.patient_id,
        detail={"flag": flag},
    )
    db.commit()
    return {"flag": flag}


def set_voucher(db: Session, actor: User, case_id: int, action: str) -> dict:
    if action not in VOUCHER_STATUS:
        raise DomainError(422, "bad_action", "Voucher action is not recognised")
    if action != "request" and actor.role not in CLINICAL:
        raise DomainError(403, "forbidden", "A navigator or clinician records that step")
    case = db.get(CareCase, case_id)
    if case is None:
        raise DomainError(404, "not_found", "Journey not found")
    _guard(db, actor, case)
    current = db.scalar(
        select(Voucher).where(Voucher.case_id == case.id).order_by(Voucher.id.desc())
    )
    status = VOUCHER_STATUS[action]
    if current is None:
        if status != "requested":
            raise DomainError(409, "bad_step", "Request the simulated voucher first")
        current = Voucher(
            case_id=case.id,
            kind="transport",
            amount_label="assumed",
            status=status,
            simulated_provider="SIMULATED_MPESA",
            created_at=clock.now(),
        )
        db.add(current)
    else:
        expected = (
            VOUCHER_ORDER[VOUCHER_ORDER.index(current.status) + 1]
            if current.status != "used"
            else None
        )
        if status != expected:
            raise DomainError(409, "bad_step", "That voucher step is out of order")
        current.status = status
    audit.record(
        db,
        actor=actor,
        action="voucher.update",
        entity_type="care_case",
        entity_id=case.id,
        patient_id=case.patient_id,
        detail={"status": status, "provider": "SIMULATED_MPESA", "amount_label": "assumed"},
    )
    db.commit()
    return {"status": current.status, "amount_label": "assumed", "provider": "SIMULATED_MPESA"}


def set_cover(db: Session, actor: User, case_id: int, status: str) -> dict:
    if actor.role not in CLINICAL:
        raise DomainError(403, "forbidden", "A navigator or clinician records a cover check")
    if status not in COVER_STATUS:
        raise DomainError(422, "bad_status", "Cover status is not recognised")
    case = db.get(CareCase, case_id)
    if case is None:
        raise DomainError(404, "not_found", "Journey not found")
    _guard(db, actor, case)
    row = CoverCheck(
        case_id=case.id,
        status=status,
        source="SIMULATED_SHA",
        created_at=clock.now(),
    )
    db.add(row)
    audit.record(
        db,
        actor=actor,
        action="cover.check",
        entity_type="care_case",
        entity_id=case.id,
        patient_id=case.patient_id,
        detail={"status": status, "source": "SIMULATED_SHA"},
    )
    db.commit()
    return {"status": status, "source": "SIMULATED_SHA"}


def set_band(db: Session, actor: User, pregnancy_id: int, device_id: str, action: str) -> dict:
    pregnancy = db.get(Pregnancy, pregnancy_id)
    if pregnancy is None:
        raise DomainError(404, "not_found", "Pregnancy not found")
    if actor.role == ROLE_CHW and pregnancy.assigned_chw_id != actor.id:
        raise DomainError(403, "forbidden", "This person is not assigned to you")
    device = find_device(db, device_id)
    if device is None:
        raise DomainError(404, "not_found", "Device not found")
    if action == "lend":
        lend_band(db, actor, device, pregnancy)
    elif action == "return":
        return_band(db, actor, device, lost=False)
    elif action == "lost":
        return_band(db, actor, device, lost=True)
    else:
        raise DomainError(422, "bad_action", "Band action is not recognised")
    return {"device_id": device.pseudonymous_device_id, "status": device.status}


def finish_device_task(db: Session, actor: User, task_id: int) -> dict:
    task = db.get(NavigatorTask, task_id)
    if task is None or task.task_type not in DEVICE_TASKS:
        raise DomainError(404, "not_found", "Device task not found")
    complete_task(db, task, actor, None)
    return {"id": task.id, "status": task.status}
