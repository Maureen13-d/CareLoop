"""Synthetic cohort for the fairness view. Not a causal study."""

import random
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.modules.followup.models import Enrolment
from app.modules.followup.register import register_followup
from app.modules.followup.schemas import RegisterIn
from app.modules.pathways.models import CareCase, CaseEvent

LANGUAGES = ("en", "sw")
CHANNELS = ("telegram", "sms", "ussd", "web")
AREAS = ("Zone A", "Zone B", "Zone C", "Zone D")


def build_cohort(db: Session, actor, n: int = 200) -> int:
    """Insert n synthetic journeys. Safe to call once on an empty follow-up table."""
    rng = random.Random(42)
    now = clock.now()
    for index in range(n):
        data = RegisterIn(
            age_band="30-34",
            area_label=AREAS[index % len(AREAS)],
            screening_type="general",
            finding="urgent" if index % 11 == 0 else "concerning",
            consent=True,
            language=LANGUAGES[index % len(LANGUAGES)],
            channel=CHANNELS[index % len(CHANNELS)],
            contact=f"07{index:08d}",
        )
        opened = register_followup(db, actor, data)
        if index % 3 == 0 and opened["case_id"]:
            delay = rng.choice((24, 48, 96, 168))
            case = db.get(CareCase, opened["case_id"])
            case.opened_at = now - timedelta(hours=delay + 6)
            case.state = "arrived"
            case.state_entered_at = case.opened_at + timedelta(hours=delay)
            db.add(
                CaseEvent(
                    case_id=case.id,
                    from_state="screened",
                    to_state="arrived",
                    occurred_at=case.state_entered_at,
                    actor_type="system",
                    note="facility_confirmed",
                )
            )
            db.commit()
        elif index % 5 == 0 and opened["case_id"]:
            case = db.get(CareCase, opened["case_id"])
            case.state = "contacted"
            db.commit()
    return n


def report(db: Session) -> dict:
    rows = db.execute(
        select(Enrolment, CareCase).join(CareCase, CareCase.id == Enrolment.case_id)
    ).all()
    arrived_states = {"arrived", "with_hospital", "closed"}
    contacted_states = arrived_states | {
        "contacted",
        "joined",
        "barrier_identified",
        "navigating",
        "visit_booked",
    }

    def pack(subset):
        total = len(subset)
        if not total:
            return {"n": 0, "percent_contacted": 0, "percent_arrived": 0}
        contacted = sum(1 for _enrol, case in subset if case.state in contacted_states)
        arrived = sum(1 for _enrol, case in subset if case.state in arrived_states)
        return {
            "n": total,
            "percent_contacted": contacted / total,
            "percent_arrived": arrived / total,
        }

    def slice_by(field: str):
        grouped: dict[str, list] = {}
        for enrolment, case in rows:
            grouped.setdefault(getattr(enrolment, field), []).append((enrolment, case))
        return {key: pack(value) for key, value in sorted(grouped.items())}

    hours = []
    for enrolment, case in rows:
        if case.state not in arrived_states:
            continue
        event = db.scalar(
            select(CaseEvent)
            .where(CaseEvent.case_id == case.id, CaseEvent.to_state == "arrived")
            .order_by(CaseEvent.id)
        )
        when = event.occurred_at if event else case.state_entered_at
        hours.append((when - case.opened_at).total_seconds() / 3600)
    ordered = sorted(hours)
    median = None
    if ordered:
        mid = len(ordered) // 2
        median = ordered[mid] if len(ordered) % 2 else (ordered[mid - 1] + ordered[mid]) / 2
    completed = sum(1 for _e, case in rows if case.state in {"with_hospital", "closed"})
    return {
        "synthetic": True,
        "n": len(rows),
        "overall": pack(rows),
        "median_hours_to_arrival": median,
        "referral_completion": (completed / len(rows)) if rows else 0,
        "by_language": slice_by("language"),
        "by_channel": slice_by("channel"),
        "by_area": slice_by("area_label"),
        "note": (
            "SYNTHETIC. Do not read contacted versus not contacted as a causal effect. "
            "Outreach starts because a visit is already late."
        ),
    }
