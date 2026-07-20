from dataclasses import dataclass

from sheet_project.engine.classes.abilities import ABILITIES


@dataclass(frozen=True)
class HitPointProgression:
    base_hp: int
    base_hp_modifier: ABILITIES
    hp_per_level: int
    hp_per_level_modifier: ABILITIES

    def calculate(self, level: int, modifiers: dict[ABILITIES, int]) -> int:
        return (
            self.base_hp
            + modifiers[self.base_hp_modifier]
            + (level - 1)
            * (
                self.hp_per_level
                + modifiers[self.hp_per_level_modifier]
            )
        )