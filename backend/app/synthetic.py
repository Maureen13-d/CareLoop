import random
from datetime import UTC, datetime, timedelta

from app.models import Case, StageEvent
from app.pathway import Stage


def generate_cases(n: int, seed: int, now: datetime | None = None) -> list[Case]:
    rng = random.Random(seed)
    now = now or datetime.now(UTC)
    stages = list(Stage)  # enum order matches the happy-path order
    cases = []
    for i in range(n):
        k = rng.randint(1, len(stages))
        path = stages[:k]
        t = now - timedelta(days=rng.randint(k, 120))
        history = []
        for s in path:
            history.append(StageEvent(stage=s, at=t))
            t = min(t + timedelta(days=rng.randint(1, 20)), now)
        cases.append(
            Case(
                id=f"case-{i + 1:04d}",
                patient_ref=f"SYN-{1000 + i}",
                stage=path[-1],
                stage_entered_at=history[-1].at,
                history=history,
            )
        )
    return cases
