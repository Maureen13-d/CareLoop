"""Phrase list. No slots, and every line is still pending clinical review."""

from app.modules.ksl.manifest import current_caption, manifest, phrase_text
from app.modules.ksl.models import KslClip, KslFacilityFlag, KslReview, KslSigner


def test_manifest_has_forty_fixed_phrases():
    rows = manifest()
    assert len(rows) == 40
    assert len({row["id"] for row in rows}) == 40
    for row in rows:
        assert row["clinical_review"] == "pending"
        text = phrase_text(row)
        assert text
        assert "{" not in text and "}" not in text
        assert current_caption(row["id"]) == text


def test_registry_tables_register():
    names = {KslSigner.__tablename__, KslClip.__tablename__, KslReview.__tablename__}
    names.add(KslFacilityFlag.__tablename__)
    assert names == {"ksl_signers", "ksl_clips", "ksl_reviews", "ksl_facility_flags"}
