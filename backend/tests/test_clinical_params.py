from app.clinical_params import DOC_PATH, extract_block, render_markdown
from app.outreach import MESSAGES
from app.pathway import SLA_DAYS, TRANSITIONS, Stage


def test_review_brief_matches_the_code():
    """If this fails, clinical parameters changed: regenerate the brief and revisit the review."""
    doc = DOC_PATH.read_text()
    assert extract_block(doc) == render_markdown(), (
        "docs/CLINICAL_REVIEW.md is out of date. From backend/, run: "
        "python -m app.clinical_params --write"
    )


def test_every_active_stage_has_clinical_parameters():
    """Adding a stage without an SLA and message wording must fail the build."""
    for stage in Stage:
        if TRANSITIONS[stage]:  # not an end state
            assert stage in SLA_DAYS, f"{stage.value} has no SLA"
            assert stage in MESSAGES, f"{stage.value} has no message wording"


def test_brief_states_it_is_unreviewed():
    assert "UNREVIEWED" in DOC_PATH.read_text()
