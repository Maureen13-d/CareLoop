from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel

from app.db import make_engine
from app.models import Case, StageEvent
from app.outreach import Channel, Kind, OutreachEvent, record_response
from app.pathway import Stage
from app.repository import Repository
from app.seed import seed_if_empty
from app.tables import CaseRow, UTCDateTime


def _case(case_id="c1", ref="SYN-1234", stage=Stage.ABNORMAL_RESULT, entered=None):
    entered = entered or datetime.now(UTC) - timedelta(days=30)
    return Case(
        id=case_id,
        patient_ref=ref,
        stage=stage,
        stage_entered_at=entered,
        history=[StageEvent(stage=stage, at=entered)],
    )


def test_case_round_trip_preserves_history_and_timezone(db):
    nairobi = timezone(timedelta(hours=3))
    t0 = datetime(2026, 1, 1, 12, tzinfo=nairobi)
    t1 = t0 + timedelta(days=2)
    case = Case(
        id="c1",
        patient_ref="SYN-1234",
        stage=Stage.ABNORMAL_RESULT,
        stage_entered_at=t1,
        history=[
            StageEvent(stage=Stage.SCREENED, at=t0),
            StageEvent(stage=Stage.ABNORMAL_RESULT, at=t1),
        ],
    )
    with Session(db) as s:
        Repository(s).save_case(case)
        s.commit()
    with Session(db) as s:
        loaded = Repository(s).get_case("c1")
    assert loaded == case  # same instants, same order
    assert loaded.stage_entered_at.tzinfo is not None  # engine math needs aware datetimes


def test_history_is_append_only(db):
    case = _case()
    with Session(db) as s:
        repo = Repository(s)
        repo.save_case(case)
        case.advance(Stage.REFERRED)
        repo.save_case(case)  # must add one entry, not duplicate the first
        s.commit()
    with Session(db) as s:
        loaded = Repository(s).get_case("c1")
    assert [h.stage for h in loaded.history] == [Stage.ABNORMAL_RESULT, Stage.REFERRED]


def test_outreach_event_round_trip(db):
    case = _case()
    event = OutreachEvent(
        case_id="c1",
        patient_ref="SYN-1234",
        stage=Stage.ABNORMAL_RESULT,
        kind=Kind.REMINDER,
        channel=Channel.SMS,
        attempt=1,
        message="hello",
        status="simulated_delivered",
        created_at=datetime.now(UTC),
    )
    with Session(db) as s:
        repo = Repository(s)
        repo.save_case(case)
        s.flush()
        repo.add_events([event])
        s.commit()
    with Session(db) as s:
        assert Repository(s).events_for_case("c1") == [event]


def test_naive_datetimes_are_rejected():
    with pytest.raises(ValueError):
        UTCDateTime().process_bind_param(datetime(2026, 1, 1), None)


@pytest.mark.parametrize(
    "ref", ["MRN-12345", "SYN-123", "SYN-12a4", "syn-1234", "SYN-1234 ", "SYN-"]
)
def test_database_rejects_non_synthetic_patient_refs(db, ref):
    row = CaseRow(id="x", patient_ref=ref, stage="screened", stage_entered_at=datetime.now(UTC))
    with Session(db) as s:
        s.add(row)
        with pytest.raises(IntegrityError):
            s.commit()


@pytest.mark.parametrize("ref", ["SYN-1234", "SYN-0000123"])
def test_database_accepts_synthetic_patient_refs(db, ref):
    row = CaseRow(id="x", patient_ref=ref, stage="screened", stage_entered_at=datetime.now(UTC))
    with Session(db) as s:
        s.add(row)
        s.commit()


def test_seed_if_empty_is_idempotent(db):
    for _ in range(2):
        with Session(db) as s:
            seed_if_empty(s)
    with Session(db) as s:
        assert Repository(s).counts()["cases"] == 25


def test_state_survives_restart(tmp_path):
    """The point of this ticket: stop the 'server', start it again, state is still there."""
    url = f"sqlite:///{tmp_path / 'careloop.db'}"
    first = make_engine(url)
    SQLModel.metadata.create_all(first)
    with Session(first) as s:
        seed_if_empty(s)
        repo = Repository(s)
        case = _case("case-r", "SYN-7777")
        log: list[OutreachEvent] = []
        record_response(case, log)
        repo.save_case(case)
        s.flush()
        repo.add_events(log)
        s.commit()
        total = repo.counts()["cases"]
    first.dispose()  # server stops

    second = make_engine(url)  # server starts again
    with Session(second) as s:
        seed_if_empty(s)  # what the lifespan does on boot: must not reseed or wipe
        repo = Repository(s)
        assert repo.counts()["cases"] == total
        restored = repo.get_case("case-r")
        assert restored is not None and restored.stage == Stage.REFERRED
        assert [e.kind for e in repo.events_for_case("case-r")] == [Kind.RESPONSE]
    second.dispose()
