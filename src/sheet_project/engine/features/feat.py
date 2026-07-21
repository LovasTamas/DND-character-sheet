from dataclasses import dataclass, field
from sheet_project.engine.features.feature import Feature


@dataclass
class Feat:
    id: str
    category: str
    name: str
    description: str

    features: list[Feature] = field(default_factory=list)
