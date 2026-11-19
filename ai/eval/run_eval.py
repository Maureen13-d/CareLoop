"""Evaluation harness for the assistant's classifier (D2).

Run from the repo root:
    python -m ai.eval.run_eval --split test
    python -m ai.eval.run_eval --split test --classifier mymodule:my_function
    python -m ai.eval.run_eval --lengths ai/eval/channel_messages.txt

A classifier is any function  classify(text: str) -> str  returning one label.
Labels: crisis, diagnosis_request, fear, cost, transport, stigma,
dont_know_where, none.

Rule for honest numbers: tune on --split dev, report only --split test.
The data is small, hand-written and synthetic. Results describe THIS set only,
not real patients.
"""
import argparse
import importlib
import json
import sys
from pathlib import Path

DATA = Path(__file__).parent / "messages.jsonl"
LABELS = ["crisis", "diagnosis_request", "fear", "cost", "transport",
          "stigma", "dont_know_where", "none"]
# SMS: one GSM-7 segment. USSD: typical screen limit; it varies by network, verify.
SMS_LIMIT = 160
USSD_LIMIT = 182


def load(split: str | None):
    rows = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [r for r in rows if split in (None, "all", r["split"])]


def load_classifier(spec: str):
    module, func = spec.split(":")
    return getattr(importlib.import_module(module), func)


def score(rows, classify):
    """Return (per-label stats, misses). Pure function so it can be tested."""
    preds = [(r, classify(r["text"])) for r in rows]
    stats = {}
    for label in LABELS:
        tp = sum(1 for r, p in preds if r["label"] == label and p == label)
        fp = sum(1 for r, p in preds if r["label"] != label and p == label)
        fn = sum(1 for r, p in preds if r["label"] == label and p != label)
        precision = tp / (tp + fp) if tp + fp else None
        recall = tp / (tp + fn) if tp + fn else None
        stats[label] = {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall}
    misses = [(r, p) for r, p in preds if r["label"] != p]
    return stats, misses


def pct(x):
    return "n/a" if x is None else f"{x:.0%}"


def check_lengths(path: str):
    """One message per line. Prefix a line with 'ussd:' or 'sms:' (default sms)."""
    bad = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        kind, _, body = line.partition(":") if line.split(":")[0] in ("sms", "ussd") else ("sms", "", line)
        limit = USSD_LIMIT if kind == "ussd" else SMS_LIMIT
        if len(body) > limit:
            bad.append((kind, len(body), limit, body[:50]))
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test", choices=["dev", "test", "all"])
    ap.add_argument("--classifier", default="ai.eval.baseline:classify")
    ap.add_argument("--lengths", help="text file of SMS/USSD messages to check")
    ap.add_argument("--min-crisis-recall", type=float, default=None,
                    help="exit with code 1 if crisis recall is below this")
    a = ap.parse_args(argv)

    if a.lengths:
        bad = check_lengths(a.lengths)
        print(f"Length check: {len(bad)} message(s) over the limit")
        for kind, n, limit, head in bad:
            print(f"  {kind} {n}>{limit}: {head}...")
        return 1 if bad else 0

    rows = load(a.split)
    stats, misses = score(rows, load_classifier(a.classifier))
    print(f"Classifier: {a.classifier} | split: {a.split} | n={len(rows)}\n")
    print("| label | n | precision | recall |")
    print("|---|---|---|---|")
    for label in LABELS:
        s = stats[label]
        print(f"| {label} | {s['tp'] + s['fn']} | {pct(s['precision'])} | {pct(s['recall'])} |")
    acc = 1 - len(misses) / len(rows)
    print(f"\nOverall accuracy: {acc:.0%} ({len(rows) - len(misses)}/{len(rows)})")
    print(f"Crisis recall: {pct(stats['crisis']['recall'])} "
          f"({stats['crisis']['fn']} crisis message(s) missed)")
    if misses:
        print("\nMisses (expected -> predicted):")
        for r, p in misses:
            print(f"  [{r['id']}] {r['label']} -> {p}: {r['text']}")
    recall = stats["crisis"]["recall"]
    if a.min_crisis_recall is not None and (recall is None or recall < a.min_crisis_recall):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())