from __future__ import annotations

from dataclasses import dataclass

from sheet_project.engine.classes.proficiencies import ARMORPROF


@dataclass(frozen=True)
class Armor:
    id: str
    name: str
    category: ARMORPROF
    base_ac: int
    ac_bonus: int
    dex_bonus: str
    strength_requirement: int | None
    stealth_disadvantage: bool
    weight: int
    cost: dict
