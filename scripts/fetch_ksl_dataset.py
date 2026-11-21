"""Download the Maseno KSL pose dataset into data/external/ksl_pose/.

The download stays off until config/ksl_dataset.yaml has
ksl_dataset.license_verified: true. Set that only after a person has read
the licence on the Zenodo record. This script does not load .npy files.
Pickled arrays can run code. Convert them in a throwaway environment with
no network and no secrets, then use only the converted numeric files.

Nothing this script writes belongs in git.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.modules.ksl.research.fetch import DatasetRefused, run  # noqa: E402
from app.modules.ksl.research.policy import ResearchDisabled, license_verified  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if "--download" not in args:
        if not license_verified(ROOT / "config" / "ksl_dataset.yaml"):
            print(
                "Research mode is off. A person must read the Zenodo licence "
                "and set ksl_dataset.license_verified to true.",
                file=sys.stderr,
            )
            return 2
        print("Licence flag is on. Re-run with --download to fetch the archive.")
        return 0
    try:
        written = run(ROOT)
    except (ResearchDisabled, DatasetRefused) as exc:
        print(exc, file=sys.stderr)
        return 2
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
