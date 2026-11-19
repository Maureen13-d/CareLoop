"""Maps between database rows and the domain models. Handlers never see ORM objects."""

from collections import defaultdict

from sqlmodel import Session, select

from app.models import Case, StageEvent
from app.outreach import OutreachEvent
from app.pathway import Stage
from app.tables import CaseRow, OutreachEventRow, StageEventRow


def _to_case(row: CaseRow, history: list[StageEventRow]) -> Case:
    return Case(
        id=row.id,
        patient_ref=row.patient_ref,
        stage=Stage(row.stage),
        stage_entered_at=row.stage_entered_at,
        history=[StageEvent(stage=Stage(h.stage), at=h.occurred_at) for h in history],
    )


def _to_event(row: OutreachEventRow) -> OutreachEvent:
    return OutreachEvent.model_validate(row.model_dump())


class Repository:
    """Methods stage changes on the session; the caller decides when to commit()."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def commit(self) -> None:
        self.session.commit()

    # ---- cases -------------------------------------------------------------------------
    def has_cases(self) -> bool:
        return self.session.exec(select(CaseRow.id).limit(1)).first() is not None

    def get_case(self, case_id: str) -> Case | None:
        row = self.session.get(CaseRow, case_id)
        if row is None:
            return None

        history = self.session.exec(
            select(StageEventRow).where(StageEventRow.case_id == case_id).order_by(StageEventRow.id)
        ).all()

        return _to_case(row, list(history))

    def list_cases(self) -> list[Case]:
        rows = self.session.exec(select(CaseRow).order_by(CaseRow.id)).all()

        by_case: dict[str, list[StageEventRow]] = defaultdict(list)
        for h in self.session.exec(select(StageEventRow).order_by(StageEventRow.id)).all():
            by_case[h.case_id].append(h)

        return [_to_case(r, by_case[r.id]) for r in rows]

    def save_case(self, case: Case) -> None:
        """Insert or update. History is append-only: only entries not yet stored are written."""
        row = self.session.get(CaseRow, case.id)
        if row is None:
            row = CaseRow(
                id=case.id,
                patient_ref=case.patient_ref,
                stage=case.stage.value,
                stage_entered_at=case.stage_entered_at,
            )
            self.session.add(row)
            self.session.flush()  # parent row before child rows
        else:
            row.stage = case.stage.value
            row.stage_entered_at = case.stage_entered_at
            self.session.add(row)

        stored = len(
            self.session.exec(
                select(StageEventRow.id).where(StageEventRow.case_id == case.id)
            ).all()
        )
        for entry in case.history[stored:]:
            self.session.add(
                StageEventRow(case_id=case.id, stage=entry.stage.value, occurred_at=entry.at)
            )

    # ---- outreach events -----------------------------------------------------------------
    def add_events(self, events: list[OutreachEvent]) -> None:
        for e in events:
            self.session.add(
                OutreachEventRow(
                    id=e.id,
                    case_id=e.case_id,
                    patient_ref=e.patient_ref,
                    stage=e.stage.value,
                    kind=e.kind.value,
                    channel=e.channel.value,
                    attempt=e.attempt,
                    message=e.message,
                    status=e.status,
                    created_at=e.created_at,
                )
            )

    def events_for_case(self, case_id: str) -> list[OutreachEvent]:
        stmt = (
            select(OutreachEventRow)
            .where(OutreachEventRow.case_id == case_id)
            .order_by(OutreachEventRow.created_at)
        )
        return [_to_event(r) for r in self.session.exec(stmt).all()]

    def load_log(self) -> list[OutreachEvent]:
        stmt = select(OutreachEventRow).order_by(OutreachEventRow.created_at)
        return [_to_event(r) for r in self.session.exec(stmt).all()]

    def recent_events(self, case_id: str | None, limit: int) -> list[OutreachEvent]:
        stmt = select(OutreachEventRow).order_by(OutreachEventRow.created_at.desc()).limit(limit)
        if case_id is not None:
            stmt = stmt.where(OutreachEventRow.case_id == case_id)
        return [_to_event(r) for r in self.session.exec(stmt).all()]

    def counts(self) -> dict[str, int]:
        return {
            "cases": len(self.session.exec(select(CaseRow.id)).all()),
            "outreach_events": len(self.session.exec(select(OutreachEventRow.id)).all()),
        }
