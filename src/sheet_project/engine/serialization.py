"""JSON-friendly serialization helpers for engine objects.

Kept separate from `Character` so the serialization *shape* concerns
(enum -> value, set -> sorted list, dataclass -> plain dict) don't bloat
the character model itself. `Character.to_dict()` is still the single
entry point the API layer calls; this module is its implementation
detail.
"""
from __future__ import annotations

import dataclasses
from enum import Enum
from typing import Any

from sheet_project.engine.features.active_feature import ActiveFeature
from sheet_project.engine.features.choice_feature import ChoiceFeature
from sheet_project.engine.features.feature import FeatureBase


def serialize_value(value: Any) -> Any:
    """Recursively convert enums/sets/dataclasses into JSON-safe values."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (set, frozenset)):
        return sorted(serialize_value(v) for v in value)
    if isinstance(value, dict):
        return {serialize_value(k): serialize_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize_value(v) for v in value]
    if dataclasses.is_dataclass(value):
        return serialize_dataclass(value)
    return value


def serialize_dataclass(obj: Any) -> dict:
    """Serialize a (frozen) dataclass's public fields only."""
    return {
        field.name: serialize_value(getattr(obj, field.name))
        for field in dataclasses.fields(obj)
    }


def serialize_feature(feature: FeatureBase, choices: dict | None = None) -> dict:
    """Serialize a Feature/ActiveFeature/ChoiceFeature with a `kind` discriminator."""
    result = {
        "id": feature.id,
        "name": feature.name,
        "desc": feature.description,
        "kind": feature.type,
    }
    if isinstance(feature, ActiveFeature):
        result["max_use"] = feature.max_use
        result["remaining_use"] = feature.remaining_use
    if isinstance(feature, ChoiceFeature):
        result["chosen_value"] = (choices or {}).get(feature.id)
    return result
