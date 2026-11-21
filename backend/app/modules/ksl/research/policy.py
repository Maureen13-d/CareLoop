"""Licence gate for the open KSL pose dataset.

Research mode stays off until a person sets ksl_dataset.license_verified
to true after reading the Zenodo record. An environment variable cannot
turn it on.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from app.core.config import REPO_ROOT

CONFIG = Path(REPO_ROOT) / "config" / "ksl_dataset.yaml"


class ResearchDisabled(RuntimeError):
    """Raised when research mode is asked to run before the licence is verified."""


def dataset_config(path: Path | None = None) -> dict:
    target = CONFIG if path is None else path
    with open(target, encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        return {"ksl_dataset": {}}
    return data


def license_verified(path: Path | None = None) -> bool:
    try:
        block = dataset_config(path).get("ksl_dataset") or {}
    except FileNotFoundError:
        return False
    return block.get("license_verified") is True


def require_license(config: dict) -> None:
    block = config.get("ksl_dataset") or {}
    if block.get("license_verified") is not True:
        raise ResearchDisabled(
            "Research mode is off. A person must read the Zenodo licence "
            "and set ksl_dataset.license_verified to true."
        )
