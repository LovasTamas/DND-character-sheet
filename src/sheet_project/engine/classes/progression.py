from dataclasses import dataclass


@dataclass
class FeatureRequirement:
    level: int
    feature_id: str
    feature_type: str | None = None
    choices: str | None = None
