from dataclasses import dataclass
from src.sheet_project.engine.backgrounds.background import AbilityChoice
from src.sheet_project.engine.features.feature import Feature


@dataclass(frozen=True)
class Species:
    id: str
    name: str

    size: str
    speed: int

    ability_choice: AbilityChoice | None

    features: list[Feature]
