from __future__ import annotations

from dataclasses import dataclass

from sheet_project.engine.features.feature import Feature


@dataclass(frozen=True)
class Race:
    id: str
    name: str
    size: str
    speed: int
    creature_type: str
    features: dict[str, Feature]
