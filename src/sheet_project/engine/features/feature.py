from dataclasses import dataclass, field
from typing import Any


@dataclass
class Feature:
    type: str

    target: str | None = None
    operation: str | None = None
    value: dict[str, Any] | None = None

    conditions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
