"""Load agent definitions from agents/roles.yaml."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

ROLES_FILE = Path(__file__).parent / "agents" / "roles.yaml"


@dataclass(frozen=True)
class Role:
    name: str
    tier: str
    system: str


def load_roles() -> dict[str, Role]:
    raw = yaml.safe_load(ROLES_FILE.read_text())
    return {name: Role(name=name, tier=cfg["tier"], system=cfg["system"].strip()) for name, cfg in raw.items()}


def role(name: str) -> Role:
    # Re-read every call so edits to roles.yaml apply without a restart.
    return load_roles()[name]
