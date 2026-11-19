"""Optional background deadline checker (ENABLE_SCHEDULER=true).
For demos it is usually clearer to advance the demo clock and run the check by hand."""

import asyncio

from app.core.db import SessionLocal
from app.modules.pathways.service import run_deadline_check


def _check_once() -> int:
    db = SessionLocal()
    try:
        return len(run_deadline_check(db))
    finally:
        db.close()


async def scheduler_loop(interval_seconds: int) -> None:
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            await asyncio.to_thread(_check_once)
        except Exception as exc:  # keep the loop alive; the next run will retry
            print(f"[scheduler] deadline check failed: {exc}")
