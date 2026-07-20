from __future__ import annotations

from dataclasses import dataclass

from sheet_project.engine.classes.abilities import ABILITIES
from sheet_project.engine.classes.proficiencies import SKILLPROF
from sheet_project.engine.features.feature import Feature


@dataclass(frozen=True)
class Background:
    id: str
    name: str
    ability_options: tuple[ABILITIES, ABILITIES, ABILITIES]
    skill_profs: set[SKILLPROF]
    tool_prof: str | None
    languages: set[str]
    feat: Feature
    equipment: list[str]
