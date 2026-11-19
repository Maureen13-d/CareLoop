"""Loop-closure metrics. Pure functions over domain objects: no database, easy to test.
Definitions (also shown in the UI)
- Outreach episode: one (case, stage) pair that received at least one automated contact
  (reminder or escalation). Contact only happens once a case is overdue, so an episode is an
  overdue stretch that outreach touched.
- Attended: the episode ended with a recorded "patient attended" response.
- These are ASSOCIATIONS, not proof of effect: a patient may have attended without the contact.
- Deliberately NOT computed: "with outreach vs without". Outreach only triggers once a case is
  already late, so contacted cases are slower by construction (selection bias).
"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from statistics import mean, median
from typing import Literal

from pydantic import BaseModel

from app.models import Case
from app.outreach import Channel, Kind, OutreachEvent
from app.pathway import SLA_DAYS, Stage, is_overdue

DISCLAIMER = (
    "Computed from synthetic data. These are associations, not evidence that outreach caused "
    "attendance, and SLA targets are unverified placeholders. Not for clinical or operational "
    "decisions."
)
Outcome = Literal["attended", "open", "unrecorded"]
CONTACT_CHANNELS = (Channel.SMS, Channel.CALL, Channel.HOME_VISIT, Channel.COORDINATOR)


class LoopClosure(BaseModel):
    contacted_episodes: int
    attended: int
    still_open: int
    unrecorded_advances: int  # data-quality flag: advanced without a response event (expect 0)
    closure_rate: float | None  # attended / contacted_episodes; None when there is no data
    median_contacts_to_attend: float | None
    attended_by_last_channel: dict[str, int]  # channel of the final contact before attending
    attended_without_outreach: int  # patients who attended before any contact was made


class Escalation(BaseModel):
    escalated: int
    escalation_rate: float | None
    recovered: int  # escalated episodes that later attended
    recovery_rate: float | None
    awaiting_coordinator: int  # escalated and still open


class TimeToReferral(BaseModel):
    completed: int  # cases that have reached "referred"
    median_days: float | None
    mean_days: float | None
    within_sla_rate: float | None
    sla_days: int
    awaiting: int  # still waiting for referral (not in the median: censored)
    awaiting_overdue: int


class Metrics(BaseModel):
    generated_at: datetime
    total_cases: int
    loop_closure: LoopClosure
    escalation: Escalation
    time_to_referral: TimeToReferral
    disclaimer: str


@dataclass(frozen=True)
class _Episode:
    outcome: Outcome
    escalated: bool
    contacts: int
    last_channel: Channel


def _rate(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else round(numerator / denominator, 4)


def _build_episodes(cases: list[Case], log: list[OutreachEvent]) -> list[_Episode]:
    contacts: dict[tuple[str, Stage], list[OutreachEvent]] = defaultdict(list)
    responded: set[tuple[str, Stage]] = set()
    for e in sorted(log, key=lambda e: e.created_at):
        key = (e.case_id, e.stage)
        if e.kind == Kind.RESPONSE:
            responded.add(key)
        else:
            contacts[key].append(e)
    by_id = {c.id: c for c in cases}
    episodes: list[_Episode] = []
    for (case_id, stage), events in contacts.items():
        case = by_id.get(case_id)
        if case is None:
            continue  # orphan event; the foreign key prevents this in the database
        outcome: Outcome
        if (case_id, stage) in responded:
            outcome = "attended"
        elif case.stage == stage:
            outcome = "open"
        else:
            outcome = "unrecorded"
        episodes.append(
            _Episode(
                outcome=outcome,
                escalated=any(e.kind == Kind.ESCALATION for e in events),
                contacts=len(events),
                last_channel=events[-1].channel,
            )
        )
    return episodes


def _entered_at(case: Case, stage: Stage) -> datetime | None:
    for h in case.history:
        if h.stage == stage:
            return h.at
    return None


def _time_to_referral(cases: list[Case], now: datetime) -> TimeToReferral:
    sla = SLA_DAYS[Stage.ABNORMAL_RESULT]
    durations: list[float] = []
    for c in cases:
        start = _entered_at(c, Stage.ABNORMAL_RESULT)
        end = _entered_at(c, Stage.REFERRED)
        if start is not None and end is not None:
            durations.append((end - start).total_seconds() / 86400)
    waiting = [c for c in cases if c.stage == Stage.ABNORMAL_RESULT]
    return TimeToReferral(
        completed=len(durations),
        median_days=round(median(durations), 1) if durations else None,
        mean_days=round(mean(durations), 1) if durations else None,
        within_sla_rate=_rate(sum(d <= sla for d in durations), len(durations)),
        sla_days=sla,
        awaiting=len(waiting),
        awaiting_overdue=sum(is_overdue(c.stage, c.stage_entered_at, now) for c in waiting),
    )


def compute_metrics(
    cases: list[Case], log: list[OutreachEvent], now: datetime | None = None
) -> Metrics:
    now = now or datetime.now(UTC)
    episodes = _build_episodes(cases, log)
    total = len(episodes)
    attended = [e for e in episodes if e.outcome == "attended"]
    escalated = [e for e in episodes if e.escalated]
    recovered = [e for e in escalated if e.outcome == "attended"]
    by_channel = Counter(e.last_channel for e in attended)
    contacts_to_attend = [e.contacts for e in attended]
    return Metrics(
        generated_at=now,
        total_cases=len(cases),
        loop_closure=LoopClosure(
            contacted_episodes=total,
            attended=len(attended),
            still_open=sum(e.outcome == "open" for e in episodes),
            unrecorded_advances=sum(e.outcome == "unrecorded" for e in episodes),
            closure_rate=_rate(len(attended), total),
            median_contacts_to_attend=(
                round(float(median(contacts_to_attend)), 1) if contacts_to_attend else None
            ),
            attended_by_last_channel={c.value: by_channel.get(c, 0) for c in CONTACT_CHANNELS},
            attended_without_outreach=sum(
                1 for e in log if e.kind == Kind.RESPONSE and e.attempt == 0
            ),
        ),
        escalation=Escalation(
            escalated=len(escalated),
            escalation_rate=_rate(len(escalated), total),
            recovered=len(recovered),
            recovery_rate=_rate(len(recovered), len(escalated)),
            awaiting_coordinator=sum(e.outcome == "open" for e in escalated),
        ),
        time_to_referral=_time_to_referral(cases, now),
        disclaimer=DISCLAIMER,
    )
