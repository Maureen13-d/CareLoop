"""Local ops for the demo database.
python -m app.cli reset [--demo]   wipe everything and re-seed synthetic data
python -m app.cli status           show row counts
"""

import argparse
import sys

from sqlmodel import Session

from app.config import settings
from app.db import engine, init_db, reset_db
from app.repository import Repository
from app.seed import seed_if_empty


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    reset = sub.add_parser("reset", help="Wipe all data and re-seed synthetic data")
    reset.add_argument("--demo", action="store_true", help="Also seed the scripted escalated case")

    sub.add_parser("status", help="Print row counts")

    args = parser.parse_args()

    if not settings.database_url.startswith("sqlite"):
        sys.exit("Refusing to run: this command only operates on a local SQLite database.")

    if args.command == "reset":
        if args.demo:
            settings.demo_scenario = True
        reset_db()
        with Session(engine) as session:
            seed_if_empty(session)
    else:
        init_db()

    with Session(engine) as session:
        counts = Repository(session).counts()

    print(f"database: {settings.database_url}")
    for name, n in counts.items():
        print(f"  {name}: {n}")


if __name__ == "__main__":
    main()
