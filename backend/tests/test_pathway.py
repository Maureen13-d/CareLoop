from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.models import Case, StageEvent
from app.pathway import InvalidTransition, Stage, can_advance, is_overdue


def _case(stage=Stage.SCREENED, ref="SYN-1234"):
    now = datetime.now(UTC)
    return Case(id="c1", patient_ref=ref, stage=stage, stage_entered_at=now,
                history=[StageEvent(stage=stage, at=now)])
def test_valid_and_invalid_transitions():
    assert can_advance(Stage.SCREENED, Stage.ABNORMAL_RESULT)
    assert not can_advance(Stage.SCREENED, Stage.TREATMENT_STARTED)
    assert not can_advance(Stage.CLOSED, Stage.SCREENED)
def test_advance_updates_history():
    c = _case()
    c.advance(Stage.ABNORMAL_RESULT)
    assert c.stage == Stage.ABNORMAL_RESULT and len(c.history) == 2
def test_advance_rejects_skipping():
    with pytest.raises(InvalidTransition):
        _case().advance(Stage.REFERRED)
def test_overdue_detection():
    now = datetime.now(UTC)
    assert is_overdue(Stage.ABNORMAL_RESULT, now - timedelta(days=8), now)
    assert not is_overdue(Stage.ABNORMAL_RESULT, now - timedelta(days=2), now)
    assert not is_overdue(Stage.CLOSED, now - timedelta(days=999), now)
def test_non_synthetic_patient_ref_rejected():
    with pytest.raises(ValidationError):
        _case(ref="MRN-12345")
