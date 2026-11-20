"""The generic follow-up pathway loads, and the cervical file is still there."""

from pathlib import Path

from app.modules.pathways.loader import load_pathway

ORDER = [
    "screened",
    "contacted",
    "joined",
    "barrier_identified",
    "navigating",
    "visit_booked",
    "arrived",
    "with_hospital",
]


def test_follow_up_pathway_shape():
    pw = load_pathway("follow_up")
    assert pw.deadlines_status == "ASSUMED"
    assert pw.initial_state == "screened"
    assert list(pw.states) == ORDER
    assert pw.closed_state == "closed"
    assert pw.declined_state == "chose_to_stop"
    assert pw.lost_state == "closed_by_person"
    assert pw.lost_requires_escalation is True
    for state in pw.states.values():
        assert state.roles
        assert state.deadline_hours > 0
    assert pw.states["arrived"].roles == ("clinician",)
    assert "chw" not in pw.states["arrived"].roles
    assert "patient" not in pw.states["arrived"].roles
    for name in ORDER[:-1]:
        assert "arrived" in pw.states[name].next or name == "arrived"


def test_cervical_and_maternal_files_remain():
    root = Path(__file__).resolve().parents[2] / "pathways"
    assert (root / "cervical_cancer.yaml").exists()
    assert (root / "maternal.yaml").exists()
    assert load_pathway().id == "cervical_cancer"
    assert load_pathway("maternal").id == "maternal"
