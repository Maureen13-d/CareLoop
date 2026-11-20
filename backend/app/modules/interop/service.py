"""Send a visit to the simulated clinic and apply the milestones it sends back.

The clinic is a separate process (integrations/mock_hospital). Nothing here talks
to a real hospital.
"""

from datetime import timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.errors import DomainError
from app.interop import HospitalRejected, build_appointment, get_milestones, send_appointment
from app.modules.audit import service as audit
from app.modules.interop.models import HospitalLink
from app.modules.pathways.loader import load_pathway
from app.modules.pathways.models import CareCase, Evidence
from app.modules.pathways.service import add_evidence, get_case, transition
from app.modules.patients.models import Patient

LOCATION = "demo-clinic"
# Milestone code from the mock hospital -> the pathway state it may move a case into.
MILESTONE_STATE = {
    "arrived": "ARRIVAL_CONFIRMED",
    "care-started": "HANDED_OFF",
}
MATERNAL_MILESTONE = {
    "arrived": "arrived",
    "care_plan_recorded": "with_hospital",
}
REQUEST_FROM = {"NAVIGATION_ACTIVE", "APPOINTMENT_BOOKED"}
MATERNAL_FROM = {"navigating", "visit_booked", "delivery_planned"}
ANTENATAL = "SYNTHETIC: antenatal visit request"


def link_for(db: Session, case_id: int) -> HospitalLink | None:
    return db.scalar(select(HospitalLink).where(HospitalLink.case_id == case_id))


def view(link: HospitalLink) -> dict:
    milestones = [item for item in link.milestones.split(",") if item]
    return {
        "case_id": link.case_id,
        "appointment_id": link.appointment_id,
        "location_ref": link.location_ref,
        "milestones": milestones,
    }


def _reject_hospital(exc: HospitalRejected) -> None:
    raise DomainError(422, "hospital_rejected", str(exc)) from exc


def _unreachable(exc: Exception) -> None:
    raise DomainError(
        503,
        "hospital_unreachable",
        "The simulated clinic is not running. Start it on port 8100 and try again.",
    ) from exc


def request_visit(db: Session, case: CareCase, actor, client: httpx.Client) -> HospitalLink:
    maternal = case.pathway_id == "maternal"
    allowed = MATERNAL_FROM if maternal else REQUEST_FROM
    if case.state not in allowed:
        raise DomainError(
            409,
            "invalid_transition",
            "A visit can be requested once a navigator is helping, or while a visit is booked.",
        )
    existing = link_for(db, case.id)
    if existing:
        return existing
    patient = db.get(Patient, case.patient_id)
    ref = patient.patient_ref if patient else f"patient-{case.patient_id}"
    start = (clock.now() + timedelta(days=2)).replace(microsecond=0).isoformat() + "Z"
    description = ANTENATAL if maternal else "SYNTHETIC: follow-up visit request"
    appointment = build_appointment(ref, LOCATION, start, description)
    try:
        appointment_id = send_appointment(client, appointment)
    except HospitalRejected as exc:
        _reject_hospital(exc)
    except httpx.HTTPError as exc:
        _unreachable(exc)
    link = HospitalLink(
        case_id=case.id,
        appointment_id=appointment_id,
        location_ref=LOCATION,
        milestones="",
        created_at=clock.now(),
    )
    db.add(link)
    db.flush()
    audit.record(
        db,
        actor=actor,
        action="hospital.request",
        entity_type="care_case",
        entity_id=case.id,
        patient_id=case.patient_id,
        detail={"appointment_id": appointment_id, "simulated": True},
    )
    if case.state == "NAVIGATION_ACTIVE":
        transition(
            db, case, "APPOINTMENT_BOOKED", actor, "Simulated clinic accepted the visit request"
        )
    elif maternal and case.state == "navigating":
        transition(db, case, "visit_booked", actor, "Simulated clinic accepted the visit request")
    else:
        db.commit()
    return link


def _apply(db: Session, case: CareCase, milestones: list[str]) -> CareCase:
    """Move the case only along transitions the pathway already allows."""
    maternal = case.pathway_id == "maternal"
    mapping = MATERNAL_MILESTONE if maternal else MILESTONE_STATE
    done_code = "care_plan_recorded" if maternal else "care-started"
    done_state = "with_hospital" if maternal else "HANDED_OFF"
    for code in milestones:
        target = mapping.get(code)
        if target is None or case.state == target:
            continue
        pathway = load_pathway(case.pathway_id)
        if pathway.is_terminal(case.state):
            break
        if target not in pathway.states[case.state].next:
            continue
        case = transition(db, case, target, None, f"Simulated clinic reported {code}")
    if done_code in milestones and case.state == done_state:
        reference = f"milestone:{done_code}"
        already = db.scalar(
            select(Evidence.id).where(Evidence.case_id == case.id, Evidence.reference == reference)
        )
        if already is None:
            note = (
                "Simulated clinic reported that a care plan was recorded."
                if maternal
                else "Simulated clinic reported that care has started."
            )
            add_evidence(
                db,
                case,
                None,
                "facility_confirmation",
                note,
                reference=reference,
            )
    return case


def sync_milestones(db: Session, case: CareCase, actor, client: httpx.Client) -> HospitalLink:
    link = link_for(db, case.id)
    if link is None:
        raise DomainError(404, "not_found", "No visit has been sent to the simulated clinic yet.")
    try:
        milestones = get_milestones(client, link.appointment_id)
    except HospitalRejected as exc:
        _reject_hospital(exc)
    except httpx.HTTPError as exc:
        _unreachable(exc)
    link.milestones = ",".join(milestones)
    case = _apply(db, get_case(db, case.id), milestones)
    audit.record(
        db,
        actor=actor,
        action="hospital.sync",
        entity_type="care_case",
        entity_id=case.id,
        patient_id=case.patient_id,
        detail={"milestones": milestones, "simulated": True},
    )
    db.commit()
    return link


def advance_clinic(db: Session, case: CareCase, actor, client: httpx.Client) -> HospitalLink:
    """Demo control: ask the pretend clinic to record its next milestone, then read it back."""
    link = link_for(db, case.id)
    if link is None:
        raise DomainError(404, "not_found", "No visit has been sent to the simulated clinic yet.")
    try:
        response = client.post(f"/demo/advance/{link.appointment_id}")
    except httpx.HTTPError as exc:
        _unreachable(exc)
    if response.status_code >= 400 and response.status_code != 409:
        raise DomainError(422, "hospital_rejected", "The simulated clinic refused to advance.")
    return sync_milestones(db, case, actor, client)
