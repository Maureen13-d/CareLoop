"""Navigator tasks.

A task is opened only when a person confirms a worry, or when the assistant hands
them to a human. Suggested keyword matches stay private until then.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.errors import DomainError
from app.modules.audit import service as audit
from app.modules.pathways.models import CareCase
from app.modules.patients.models import Patient
from app.modules.tasks.models import NavigatorTask

COPY = {
    "navigator_followup": (
        "Worry confirmed",
        "The person confirmed a worry. Contact them and agree a next step.",
    ),
    "navigator_callback": (
        "Call requested",
        "The person asked for a call back.",
    ),
    "counsellor_urgent": (
        "Urgent handoff",
        "The person may be in crisis. A counsellor should take over now.",
    ),
    "counsellor_contact": (
        "Counsellor check-in",
        "The person is distressed. A counsellor should reach out.",
    ),
    "sms_undelivered": (
        "Text not delivered",
        "A reminder could not be delivered. Find another way to reach the person.",
    ),
    "appointment_change": (
        "Change a visit",
        "The person asked to change the time of a visit.",
    ),
    "maternal_warning": (
        "A check needs a person",
        "A home check needs a navigator. Decision support only. PENDING CLINICAL REVIEW.",
    ),
    "chw_cuff": (
        "Please take a cuff reading today",
        "The band asked for a cuff reading. The band does not measure that itself.",
    ),
    "chw_battery": (
        "Charge or swap a device",
        "A device battery is low.",
    ),
    "device_offline": (
        "Device offline",
        "A device has not been seen within the assumed window.",
    ),
    "followup_urgent": (
        "Go to the clinic now",
        "A check-in needs a person. PENDING CLINICAL REVIEW.",
    ),
    "followup_review": (
        "A person should follow up",
        "The message was unclear or asked for something the guide cannot answer.",
    ),
    "followup_barrier": (
        "A barrier was confirmed",
        "The person confirmed what is stopping them.",
    ),
    "followup_escalate": (
        "CHW escalation",
        "A community health worker asked a clinician to take this.",
    ),
    "followup_unreached": (
        "No reply to check-ins",
        "Check-ins went unanswered. This is a problem to solve, not a fault.",
    ),
    "followup_unreachable": (
        "Telegram unreachable, try another channel.",
        "The bot could not deliver. Try a phone call or a home visit.",
    ),
    "followup_ksl": (
        "Signed clip missing",
        "No approved signed clip for this line. A person should help.",
    ),
}


def should_open_task(response) -> bool:
    if not getattr(response, "suggested_task", None):
        return False
    if response.needs_human:
        return True
    return any(flag.status == "confirmed" for flag in response.barrier_flags)


def create_task(
    db: Session,
    *,
    task_type: str,
    priority: str = "normal",
    case_id: int | None = None,
    source: str = "assistant",
    actor=None,
) -> NavigatorTask:
    """Open a task. An open task of the same type on the same case is reused."""
    if case_id is not None:
        existing = db.scalar(
            select(NavigatorTask).where(
                NavigatorTask.case_id == case_id,
                NavigatorTask.task_type == task_type,
                NavigatorTask.status == "open",
            )
        )
        if existing:
            return existing
    title, summary = COPY.get(task_type, ("Navigator task", "A person needs a human follow-up."))
    task = NavigatorTask(
        case_id=case_id,
        task_type=task_type,
        priority=priority,
        title=title,
        summary=summary,
        status="open",
        source=source,
        created_at=clock.now(),
    )
    db.add(task)
    db.flush()
    case = db.get(CareCase, case_id) if case_id else None
    audit.record(
        db,
        actor=actor,
        action="task.open",
        entity_type="navigator_task",
        entity_id=task.id,
        patient_id=case.patient_id if case else None,
        detail={"task_type": task_type, "priority": priority, "source": source},
    )
    return task


def complete_task(
    db: Session, task: NavigatorTask, actor, note: str | None = None
) -> NavigatorTask:
    if task.status == "done":
        raise DomainError(409, "already_done", "This task is already done")
    task.status = "done"
    task.completed_at = clock.now()
    task.completed_by = actor.id if actor else None
    case = db.get(CareCase, task.case_id) if task.case_id else None
    audit.record(
        db,
        actor=actor,
        action="task.complete",
        entity_type="navigator_task",
        entity_id=task.id,
        patient_id=case.patient_id if case else None,
        detail={"note": note} if note else None,
    )
    db.commit()
    return task


def task_view(db: Session, task: NavigatorTask) -> dict:
    case = db.get(CareCase, task.case_id) if task.case_id else None
    patient = db.get(Patient, case.patient_id) if case else None
    return {
        "id": task.id,
        "case_id": task.case_id,
        "patient_ref": patient.patient_ref if patient else None,
        "patient_display_name": patient.display_name if patient else None,
        "task_type": task.task_type,
        "priority": task.priority,
        "title": task.title,
        "summary": task.summary,
        "status": task.status,
        "source": task.source,
        "created_at": task.created_at,
    }
