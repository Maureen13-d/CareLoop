"""Checks that the evaluation data is well formed (not a quality test of any model)."""
from ai.eval.run_eval import LABELS, load, score


def test_labels_ids_and_splits_are_valid():
    rows = load("all")
    assert len({r["id"] for r in rows}) == len(rows)
    for label in LABELS:
        for split in ("dev", "test"):
            n = sum(1 for r in rows if r["label"] == label and r["split"] == split)
            assert n >= 4, f"{label}/{split} has only {n}"
    assert all(r["label"] in LABELS for r in rows)


def test_score_counts_precision_and_recall():
    rows = [
        {"id": "a", "text": "x", "label": "crisis", "split": "test"},
        {"id": "b", "text": "y", "label": "crisis", "split": "test"},
        {"id": "c", "text": "z", "label": "none", "split": "test"},
    ]
    stats, misses = score(rows, lambda t: "crisis" if t in ("x", "z") else "none")
    assert stats["crisis"]["recall"] == 0.5
    assert stats["crisis"]["precision"] == 0.5
    assert len(misses) == 2