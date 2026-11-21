"""CHW worklist. A worsening flag always ranks first. Reasons are labels."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.errors import DomainError
from app.modules.audit import service as audit
from app.modules.auth.models import ROLE_CHW
from app.modules.followup.models import Enrolment
from app.modules.followup.texts import checkin_rules, worklist_rules
from app.modules.pathways.models import CareCase
from app.modules.pathways.service import transition
from app.modules.tasks.service import create_task

CHASE_DONE = {"arrived", "with_hospital", "closed", "chose_to_stop", "closed_by_person"}
BARRIER_WORDS = {
    "transport": "transport fare",
    "cost": "cost",
    "fear": "fear",
    "stigma": "stigma",
    "where": "not knowing where to go",
    "interpreter": "interpreter needed",
}
STAFF = {"navigator", "clinician", "admin", "program_manager", "chw"}


def _days(opened, now) -> int:
    return max(0, (now - opened).days)


def _missed_limit(enrolment: Enrolment) -> int:
    rules = checkin_rules()
    if enrolment.language == "ksl":
        return int(rules["ksl_unreached_after"])
    return int(rules["unreached_after"])


def reason_for(enrolment: Enrolment, days: int) -> str:
    if enrolment.symptom_flag == "worse":
        return "reported worse symptoms"
    if enrolment.barrier_label:
        word = BARRIER_WORDS.get(enrolment.barrier_label, enrolment.barrier_label)
        return f"barrier: {word}"
    if enrolment.missed_replies >= _missed_limit(enrolment):
        return f"no reply to {enrolment.missed_replies} check-ins"
    return f"not arrived, {days} days"


def action_for(enrolment: Enrolment) -> str:
    if enrolment.symptom_flag == "worse":
        return "escalate to clinician"
    if enrolment.barrier_label in {"transport", "cost"}:
        return "transport support"
    if enrolment.barrier_label in {"fear", "stigma"}:
        return "counsellor"
    if enrolment.barrier_label == "where":
        if enrolment.language == "ksl":
            return "home visit with a KSL-aware CHW"
        return "home visit"
    if enrolment.barrier_label == "interpreter":
        return "book interpreter"
    if enrolment.language == "ksl":
        return "text or video"
    return "call"


def _score(enrolment: Enrolment, case: CareCase, days: int, now) -> int:
    rules = worklist_rules()["score"]
    score = days * int(rules["per_day"])
    if enrolment.finding == "urgent":
        score += int(rules["urgent_finding"])
    if case.deadline_at is not None and case.deadline_at < now:
        score += int(rules["overdue"])
    if enrolment.missed_replies >= _missed_limit(enrolment):
        score += int(rules["unreached"])
    if enrolment.barrier_label:
        score += int(rules["barrier"])
    return score


def list_work(db: Session, actor) -> dict:
    if actor.role not in STAFF:
        raise DomainError(403, "forbidden", "Role is not allowed to see this worklist")
    now = clock.now()
    stmt = (
        select(Enrolment, CareCase)
        .join(CareCase, CareCase.id == Enrolment.case_id)
        .where(CareCase.state.not_in(list(CHASE_DONE)))
    )
    if actor.role == ROLE_CHW:
        stmt = stmt.where(
            (Enrolment.assigned_chw_id == actor.id) | (Enrolment.assigned_chw_id.is_(None))
        )
    pairs = db.execute(stmt).all()
    rows = []
    for enrolment, case in pairs:
        days = _days(enrolment.opened_at, now)
        overdue = case.deadline_at is not None and case.deadline_at < now
        rows.append(
            {
                "case_id": case.id,
                "public_id": enrolment.public_id,
                "days_since_screening": days,
                "state": case.state,
                "reason": reason_for(enrolment, days),
                "recommended_action": action_for(enrolment),
                "overdue": overdue,
                "worse": enrolment.symptom_flag == "worse",
                "unreached": enrolment.missed_replies >= 3,
                "_score": _score(enrolment, case, days, now),
                "_days": days,
            }
        )
    rows.sort(
        key=lambda row: (
            0 if row["worse"] else 1,
            -row["_score"],
            -row["_days"],
            row["public_id"],
        )
    )
    visible = [
        {key: value for key, value in row.items() if not key.startswith("_")} for row in rows
    ]
    return {
        "synthetic": True,
        "review": "PENDING CLINICAL REVIEW",
        "counts": {
            "open": len(visible),
            "overdue": sum(1 for row in visible if row["overdue"]),
            "worse": sum(1 for row in visible if row["worse"]),
            "unreached": sum(1 for row in visible if row["unreached"]),
        },
        "rows": visible,
    }


def _assigned(db: Session, actor, case_id: int) -> tuple[Enrolment, CareCase]:
    enrolment = db.scalar(select(Enrolment).where(Enrolment.case_id == case_id))
    case = db.get(CareCase, case_id)
    if enrolment is None or case is None or case.pathway_id != "follow_up":
        raise DomainError(404, "not_found", "Case not found")
    if actor.role == ROLE_CHW and enrolment.assigned_chw_id not in (None, actor.id):
        raise DomainError(403, "forbidden", "This person is assigned to someone else")
    if actor.role not in STAFF:
        raise DomainError(403, "forbidden", "Role is not allowed to do this")
    return enrolment, case


def claim(db: Session, actor, case_id: int) -> dict:
    enrolment, _case = _assigned(db, actor, case_id)
    if actor.role != ROLE_CHW:
        raise DomainError(403, "forbidden", "Only a community health worker can claim")
    if enrolment.assigned_chw_id not in (None, actor.id):
        raise DomainError(403, "forbidden", "This person is assigned to someone else")
    enrolment.assigned_chw_id = actor.id
    audit.record(
        db,
        actor=actor,
        action="followup.claim",
        entity_type="followup",
        entity_id=enrolment.id,
        patient_id=enrolment.patient_id,
        detail={"label": "claim"},
    )
    db.commit()
    return {"ok": True, "label": "claim"}


def log_attempt(db: Session, actor, case_id: int) -> dict:
    enrolment, case = _assigned(db, actor, case_id)
    audit.record(
        db,
        actor=actor,
        action="followup.contact_attempt",
        entity_type="followup",
        entity_id=enrolment.id,
        patient_id=enrolment.patient_id,
        detail={"label": "contact_attempt"},
    )
    if case.state == "screened":
        transition(db, case, "contacted", actor, "contact_attempt")
    else:
        db.commit()
    return {"ok": True, "label": "contact_attempt"}


def escalate(db: Session, actor, case_id: int) -> dict:
    enrolment, case = _assigned(db, actor, case_id)
    task = create_task(
        db,
        task_type="followup_escalate",
        priority="high",
        case_id=case.id,
        source="worklist",
        actor=actor,
    )
    audit.record(
        db,
        actor=actor,
        action="followup.escalate",
        entity_type="followup",
        entity_id=enrolment.id,
        patient_id=enrolment.patient_id,
        detail={"label": "escalate"},
    )
    db.commit()
    return {"ok": True, "task_id": task.id, "label": "escalate"}


def record_outcome(db: Session, actor, case_id: int, label: str) -> dict:
    enrolment, _case = _assigned(db, actor, case_id)
    audit.record(
        db,
        actor=actor,
        action="followup.outcome",
        entity_type="followup",
        entity_id=enrolment.id,
        patient_id=enrolment.patient_id,
        detail={"label": label},
    )
    db.commit()
    return {"ok": True, "label": label}
