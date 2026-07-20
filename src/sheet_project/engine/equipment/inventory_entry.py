from __future__ import annotations

from dataclasses import dataclass

from sheet_project.engine.equipment.armor import Armor
from sheet_project.engine.equipment.item import Item
from sheet_project.engine.equipment.weapon import Weapon


@dataclass
class InventoryEntry:
    item: Weapon | Armor | Item
    quantity: int = 1
