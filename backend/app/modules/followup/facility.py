"""Facility view. IDs and labels only. A human records arrival and lost-to-follow-up."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.errors import DomainError
from app.modules.followup.models import Enrolment
from app.modules.pathways.models import CareCase, CaseEvent, Escalation
from app.modules.pathways.service import close_case, mark_lost, transition

ARRIVED = {"arrived", "with_hospital", "closed"}
TERMINAL = {"closed", "chose_to_stop", "closed_by_person"}
READERS = {"clinician", "navigator", "program_manager", "admin"}


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def _bucket(days: float) -> str:
    if days <= 2:
        return "0-2"
    if days <= 7:
        return "3-7"
    if days <= 14:
        return "8-14"
    return "15+"


def summary(db: Session, actor) -> dict:
    if actor.role not in READERS:
        raise DomainError(403, "forbidden", "Role is not allowed to see the facility view")
    now = clock.now()
    pairs = db.execute(
        select(Enrolment, CareCase)
        .join(CareCase, CareCase.id == Enrolment.case_id)
        .where(CareCase.pathway_id == "follow_up")
    ).all()
    funnel: dict[str, int] = {}
    hours = []
    buckets = {"0-2": 0, "3-7": 0, "8-14": 0, "15+": 0}
    aging = []
    lost = []
    arrived_count = 0
    for enrolment, case in pairs:
        funnel[case.state] = funnel.get(case.state, 0) + 1
        if case.state in ARRIVED:
            arrived_count += 1
            event = db.scalar(
                select(CaseEvent)
                .where(CaseEvent.case_id == case.id, CaseEvent.to_state == "arrived")
                .order_by(CaseEvent.id)
            )
            when = event.occurred_at if event else case.state_entered_at
            delta_hours = (when - case.opened_at).total_seconds() / 3600
            hours.append(delta_hours)
            bucket = _bucket(delta_hours / 24)
            buckets[bucket] += 1
        still_out = case.state not in ARRIVED and case.state not in TERMINAL
        if still_out:
            days = max(0, (now - enrolment.opened_at).days)
            aging.append({"public_id": enrolment.public_id, "days": days, "state": case.state})
            has_escalation = (
                db.scalar(select(Escalation.id).where(Escalation.case_id == case.id)) is not None
            )
            if has_escalation:
                lost.append(
                    {
                        "public_id": enrolment.public_id,
                        "case_id": case.id,
                        "state": case.state,
                    }
                )
    total = len(pairs)
    aging.sort(key=lambda row: (-row["days"], row["public_id"]))
    return {
        "synthetic": True,
        "review": "PENDING CLINICAL REVIEW",
        "funnel": funnel,
        "percent_arrived": (arrived_count / total) if total else 0,
        "median_hours_to_arrival": _median(hours),
        "distribution_days": buckets,
        "aging": aging,
        "lost_queue": lost,
        "note": "Outreach is not a causal comparison. A person is chased because the visit is already late.",
    }


def timeline(db: Session, actor, public_id: str) -> dict:
    if actor.role not in READERS:
        raise DomainError(403, "forbidden", "Role is not allowed to see the facility view")
    enrolment = db.scalar(select(Enrolment).where(Enrolment.public_id == public_id))
    if enrolment is None or enrolment.case_id is None:
        raise DomainError(404, "not_found", "Case not found")
    events = db.scalars(
        select(CaseEvent).where(CaseEvent.case_id == enrolment.case_id).order_by(CaseEvent.id)
    ).all()
    items = [{"label": event.to_state, "at": event.occurred_at.isoformat()} for event in events]
    if enrolment.barrier_label:
        items.append({"label": f"barrier:{enrolment.barrier_label}", "at": None})
    return {"synthetic": True, "public_id": public_id, "items": items}


def confirm_arrival(db: Session, actor, case_id: int):
    case = db.get(CareCase, case_id)
    if case is None or case.pathway_id != "follow_up":
        raise DomainError(404, "not_found", "Case not found")
    if case.state in ARRIVED or case.state in TERMINAL:
        raise DomainError(409, "already_arrived", "Arrival is already recorded")
    if actor is not None and actor.role not in {"clinician", "admin"}:
        raise DomainError(403, "forbidden", "Only facility staff can record arrival")
    mover = actor if actor is not None and actor.role == "clinician" else None
    return transition(db, case, "arrived", mover, "facility_confirmed")


def care_started(db: Session, actor, case_id: int):
    case = db.get(CareCase, case_id)
    if case is None or case.pathway_id != "follow_up":
        raise DomainError(404, "not_found", "Case not found")
    if actor is None or actor.role != "clinician":
        raise DomainError(403, "forbidden", "Only facility staff can record this")
    return transition(db, case, "with_hospital", actor, "care_started")


def close_with_evidence(db: Session, actor, case_id: int):
    case = db.get(CareCase, case_id)
    if case is None or case.pathway_id != "follow_up":
        raise DomainError(404, "not_found", "Case not found")
    return close_case(
        db,
        case,
        actor,
        evidence_type="facility_confirmation",
        description="facility_confirmation",
    )


def lose(db: Session, actor, case_id: int):
    case = db.get(CareCase, case_id)
    if case is None or case.pathway_id != "follow_up":
        raise DomainError(404, "not_found", "Case not found")
    if actor is None or actor.role not in {"navigator", "clinician"}:
        raise DomainError(403, "forbidden", "A human must decide lost to follow-up")
    return mark_lost(db, case, actor, "human_decision")
