from __future__ import annotations

from dataclasses import dataclass

from sheet_project.engine.classes.proficiencies import WEPPROF


@dataclass(frozen=True)
class Weapon:
    id: str
    name: str
    category: WEPPROF
    type: str
    damage: dict
    versatile_damage: str | None
    properties: frozenset[str]
    mastery: str | None
    range: dict | None
    weight: int
    cost: dict
