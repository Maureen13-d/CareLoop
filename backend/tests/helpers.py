from sqlmodel import Session

from app.db import engine
from app.models import Case
from app.outreach import OutreachEvent
from app.repository import Repository


def put_case(case: Case, events: list[OutreachEvent] | None = None) -> None:
    """Write a case (and optional outreach events) straight to the test database."""
    with Session(engine) as session:
        repo = Repository(session)
        repo.save_case(case)
        session.flush()  # case before events (foreign key)
        repo.add_events(events or [])
        session.commit()
