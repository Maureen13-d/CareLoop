"""Loads care pathway definitions (pathways/*.yaml) and validates them."""

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from app.core.config import settings


@dataclass(frozen=True)
class StateDef:
    name: str
    label: str
    owner_department: str
    deadline_hours: int
    next: tuple[str, ...]
    roles: tuple[str, ...]


@dataclass(frozen=True)
class Pathway:
    id: str
    name: str
    version: str
    deadlines_status: str
    initial_state: str
    states: dict[str, StateDef]
    terminal_states: dict[str, str]
    closable_from: tuple[str, ...]
    evidence_types: tuple[str, ...]
    closure_roles: tuple[str, ...]
    lost_roles: tuple[str, ...]
    lost_requires_escalation: bool
    second_level_after_hours: int
    urgent_starts_at_level: int
    raw: dict = field(default_factory=dict, compare=False, repr=False)

    def is_terminal(self, state: str) -> bool:
        return state in self.terminal_states


class PathwayError(Exception):
    pass


def _build(data: dict) -> Pathway:
    states = {
        name: StateDef(
            name=name,
            label=s["label"],
            owner_department=s["owner_department"],
            deadline_hours=int(s["deadline_hours"]),
            next=tuple(s.get("next", [])),
            roles=tuple(s["roles"]),
        )
        for name, s in data["states"].items()
    }
    terminal = dict(data["terminal_states"])
    if data["initial_state"] not in states:
        raise PathwayError("initial_state is not a defined state")
    for state in states.values():
        for target in state.next:
            if target not in states:
                raise PathwayError(f"{state.name} points to unknown state {target}")
    for name in data["closure"]["closable_from"]:
        if name not in states:
            raise PathwayError(f"closable_from has unknown state {name}")
    return Pathway(
        id=data["id"],
        name=data["name"],
        version=str(data["version"]),
        deadlines_status=data.get("deadlines_status", "ASSUMED"),
        initial_state=data["initial_state"],
        states=states,
        terminal_states=terminal,
        closable_from=tuple(data["closure"]["closable_from"]),
        evidence_types=tuple(data["closure"]["evidence_types"]),
        closure_roles=tuple(data["closure"]["roles"]),
        lost_roles=tuple(data["lost_to_follow_up"]["roles"]),
        lost_requires_escalation=bool(
            data["lost_to_follow_up"].get("requires_prior_escalation", True)
        ),
        second_level_after_hours=int(data["escalation"]["second_level_after_hours"]),
        urgent_starts_at_level=int(data["escalation"]["urgent_starts_at_level"]),
        raw=data,
    )


@lru_cache(maxsize=8)
def load_pathway(pathway_id: str = "cervical_cancer") -> Pathway:
    path = Path(settings.pathways_dir) / f"{pathway_id}.yaml"
    if not path.exists():
        raise PathwayError(f"Pathway file not found: {path}")
    with open(path, encoding="utf-8") as handle:
        return _build(yaml.safe_load(handle))
