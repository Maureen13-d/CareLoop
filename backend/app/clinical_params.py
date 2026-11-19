"""The clinical parameters a reviewer must sign off on, rendered from the code itself.
    python -m app.clinical_params            print them as Markdown
    python -m app.clinical_params --write    refresh the block inside docs/CLINICAL_REVIEW.md
A test fails if the brief drifts from the code, so changing any of these values forces the
review brief (and the review) to be revisited.
"""

import argparse
import re
from pathlib import Path

from app.outreach import COOLDOWN_DAYS, LADDER, MESSAGES
from app.pathway import SLA_DAYS, TRANSITIONS, Stage

DOC_PATH = Path(__file__).resolve().parents[2] / "docs" / "CLINICAL_REVIEW.md"
START = "<!-- params:start -->"
END = "<!-- params:end -->"


def _label(value: str) -> str:
    return value.replace("_", " ")


def render_markdown() -> str:
    order = list(Stage)
    out = [
        "**A. Stages, timeframes and allowed transitions**",
        "",
        "| Stage | Flagged overdue after (days) | Can move to |",
        "|---|---|---|",
    ]
    for stage in order:
        sla = SLA_DAYS.get(stage)
        targets = sorted(TRANSITIONS[stage], key=order.index)
        nxt = ", ".join(_label(t.value) for t in targets) or "(none, end of pathway)"
        out.append(f"| {_label(stage.value)} | {sla if sla is not None else 'n/a'} | {nxt} |")

    out += ["", "**B. Outreach ladder**", "", "| Contact # | Channel |", "|---|---|"]
    for i, channel in enumerate(LADDER, start=1):
        out.append(f"| {i} | {_label(channel.value)} |")
    out.append(
        f"| {len(LADDER) + 1} | hand-off to a care coordinator; automated outreach then stops |"
    )

    out += [
        "",
        f"Minimum gap between contacts: **{COOLDOWN_DAYS} days**. "
        "The ladder restarts when the case moves to a new stage.",
        "",
        "**C. Message wording** (the same text is used for every reminder channel)",
        "",
        "| Stage | Message |",
        "|---|---|",
    ]
    for stage in order:
        if stage in MESSAGES:
            out.append(f"| {_label(stage.value)} | {MESSAGES[stage]} |")

    return "\n".join(out)


def extract_block(doc: str) -> str:
    m = re.search(re.escape(START) + r"\n(.*?)\n" + re.escape(END), doc, re.DOTALL)
    if m is None:
        raise ValueError("params markers not found in the review brief")
    return m.group(1)


def splice_block(doc: str, block: str) -> str:
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if len(pattern.findall(doc)) != 1:
        raise ValueError("expected exactly one pair of params markers in the review brief")
    return pattern.sub(lambda _: f"{START}\n{block}\n{END}", doc)


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.clinical_params")
    parser.add_argument("--write", action="store_true", help=f"update {DOC_PATH.name}")
    args = parser.parse_args()
    block = render_markdown()
    if args.write:
        DOC_PATH.write_text(splice_block(DOC_PATH.read_text(), block))
        print(f"updated {DOC_PATH}")
    else:
        print(block)


if __name__ == "__main__":
    main()
