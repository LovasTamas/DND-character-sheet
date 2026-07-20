from __future__ import annotations

from dataclasses import dataclass

from sheet_project.engine.classes.abilities import ABILITIES
from sheet_project.engine.classes.proficiencies import ARMORPROF, WEPPROF
from sheet_project.engine.classes.hitpoints import HitPointProgression
from sheet_project.engine.features.active_feature import ActiveFeature
from sheet_project.engine.features.choice_feature import ChoiceFeature
from sheet_project.engine.features.feature import Feature


@dataclass(frozen=True)
class CharacterClass:
    class_name: str

    hitpoints: HitPointProgression

    armor_profs: set[ARMORPROF]
    weapon_profs: set[WEPPROF]

    saving_throw_profs: set[ABILITIES]
    features: set[Feature|ActiveFeature|ChoiceFeature]
