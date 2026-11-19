from sqlmodel import Session

from app.config import settings
from app.demo import DEMO_CASE_ID, seed_demo_scenario
from app.models import Case
from app.outreach import OutreachEvent
from app.repository import Repository
from app.synthetic import generate_cases


def seed_if_empty(session: Session) -> None:
    """Seed synthetic data on first run only. A restart must never overwrite saved state."""
    repo = Repository(session)

    if not repo.has_cases():
        for case in generate_cases(settings.seed_cases, settings.seed):
            repo.save_case(case)

    if settings.demo_scenario and repo.get_case(DEMO_CASE_ID) is None:
        store: dict[str, Case] = {}
        log: list[OutreachEvent] = []
        seed_demo_scenario(store, log)

        for case in store.values():
            repo.save_case(case)
        session.flush()  # cases before their events (foreign key)
        repo.add_events(log)

    session.commit()
