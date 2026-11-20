"""The held-out maternal numbers are reported as measured. Do not retune the lexicon to lift them."""

import json

from app.core.config import REPO_ROOT
from app.modules.maternal.evaluate import score

TEST = REPO_ROOT / "ai" / "eval" / "maternal_test.jsonl"
DEV = REPO_ROOT / "ai" / "eval" / "maternal_dev.jsonl"


def test_the_held_out_set_is_separate_and_large_enough():
    test_rows = [
        json.loads(line) for line in TEST.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    dev_rows = [
        json.loads(line) for line in DEV.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    assert len(test_rows) >= 60
    assert sum(1 for row in test_rows if row["label"] == "red") >= 20
    assert sum(1 for row in test_rows if row["label"] in {"crisis", "distress"}) >= 10
    assert {row["text"] for row in test_rows}.isdisjoint({row["text"] for row in dev_rows})


def test_reported_scores_match_a_fresh_run():
    result = score(TEST)
    assert result["n"] == 66
    assert result["correct"] == 57
    assert result["accuracy"] == 0.8636
    assert result["red_hits"] == 23
    assert result["labelled_red"] == 26
    assert result["red_recall"] == 0.8846
    assert result["false_alarm_rate"] == 0.0
    assert [row["id"] for row in result["misses"]] == [
        "t57",
        "t58",
        "t59",
        "t60",
        "t61",
        "t62",
        "t63",
        "t64",
        "t65",
    ]
