"""Every-other-day check-in until arrival. Missed replies raise priority. Never reassures."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.modules.audit import service as audit
from app.modules.followup.conversation import log_outbound
from app.modules.followup.discreet import problems
from app.modules.followup.models import Enrolment
from app.modules.followup.texts import checkin_rules, fit, line
from app.modules.followup.vault import contact_for_send
from app.modules.pathways.models import CareCase
from app.modules.tasks.service import create_task

DONE = {"arrived", "with_hospital", "closed", "chose_to_stop", "closed_by_person"}


def _quiet(now, rules: dict) -> bool:
    hour = now.hour
    start = int(rules["quiet_start_hour"])
    end = int(rules["quiet_end_hour"])
    return hour >= start or hour < end


def run_checkins(db: Session, now=None) -> int:
    now = now or clock.now()
    rules = checkin_rules()
    if _quiet(now, rules):
        return 0
    cadence = timedelta(hours=int(rules["cadence_hours"]))
    cap = int(rules["max_attempts"])
    unreached_after = int(rules["unreached_after"])
    sent = 0
    rows = db.execute(
        select(Enrolment, CareCase).join(CareCase, CareCase.id == Enrolment.case_id)
    ).all()
    for enrolment, case in rows:
        if case.pathway_id != "follow_up" or case.state in DONE:
            continue
        if enrolment.messages_stopped:
            continue
        if contact_for_send(db, enrolment.public_id) is None:
            continue
        if enrolment.checkin_attempts >= cap:
            continue
        if enrolment.last_checkin_at and now - enrolment.last_checkin_at < cadence:
            continue
        enrolment.checkin_attempts += 1
        enrolment.missed_replies = enrolment.checkin_attempts
        enrolment.last_checkin_at = now
        if enrolment.language == "ksl":
            threshold = int(rules.get("ksl_unreached_after", 1))
        else:
            threshold = unreached_after
        if enrolment.missed_replies >= threshold:
            create_task(
                db,
                task_type="followup_unreached",
                priority="high",
                case_id=case.id,
                source="checkin",
            )
        body = fit(line("checkin", enrolment.language), enrolment.channel)
        if problems(body):
            continue
        window_open = enrolment.window_open_until is not None and enrolment.window_open_until > now
        mode = "freeform" if window_open else "template"
        log_outbound(db, enrolment.public_id, enrolment.channel, "checkin", mode, body)
        if enrolment.channel == "telegram":
            from app.modules.followup.telegram import push_checkin

            push_checkin(db, enrolment)
        audit.record(
            db,
            actor=None,
            action="followup.checkin",
            entity_type="followup",
            entity_id=enrolment.id,
            patient_id=enrolment.patient_id,
            detail={"label": "checkin", "mode": mode},
        )
        sent += 1
    db.commit()
    return sent
