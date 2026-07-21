from __future__ import annotations

from dataclasses import dataclass

from sheet_project.engine.classes.abilities import ABILITIES
from sheet_project.engine.classes.proficiencies import SKILLPROF
from sheet_project.engine.features.feat import Feat


@dataclass(frozen=True)
class AbilityChoice:
    options: tuple[ABILITIES, ...]
    count: int


@dataclass(frozen=True)
class Background:
    id: str
    name: str
    ability_choice: AbilityChoice

    skill_profs: set[SKILLPROF]
    tool_profs: set[str]
    languages: set[str]

    feats: list[Feat]
    equipment: list[str]
