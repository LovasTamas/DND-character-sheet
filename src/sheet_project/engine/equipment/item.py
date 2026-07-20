from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    id: str
    name: str
    kind: str
    weight: int
    cost: dict
