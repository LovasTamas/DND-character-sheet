from __future__ import annotations

import json

from sheet_project.engine.equipment.armor import Armor
from sheet_project.engine.equipment.armor_loader import ArmorLoader
from sheet_project.engine.equipment.item import Item
from sheet_project.engine.equipment.item_loader import ItemLoader
from sheet_project.engine.equipment.weapon import Weapon
from sheet_project.engine.equipment.weapon_loader import WeaponLoader
from sheet_project.engine.paths import DATA_DIR


class EquipmentResolver:
    def __init__(self):
        with open(DATA_DIR / "weapons.json", "r", encoding="utf-8") as f:
            self._weapons_raw = json.load(f)["weapons"]
        with open(DATA_DIR / "armors.json", "r", encoding="utf-8") as f:
            self._armors_raw = json.load(f)["armors"]
        with open(DATA_DIR / "items.json", "r", encoding="utf-8") as f:
            self._items_raw = json.load(f)["items"]

    def resolve(self, ids: list[str]) -> list[Weapon | Armor | Item]:
        """Resolve a list of equipment ids into their dataclass instances.

        Looks up each id in weapons.json, then armors.json, then items.json
        (in that order). Raises KeyError("Unknown equipment id: <id>") if not
        found in any catalog.
        """
        resolved: list[Weapon | Armor | Item] = []
        for equipment_id in ids:
            if equipment_id in self._weapons_raw:
                resolved.append(WeaponLoader._build_weapon(self._weapons_raw[equipment_id]))
            elif equipment_id in self._armors_raw:
                resolved.append(ArmorLoader._build_armor(self._armors_raw[equipment_id]))
            elif equipment_id in self._items_raw:
                resolved.append(ItemLoader._build_item(self._items_raw[equipment_id]))
            else:
                raise KeyError(f"Unknown equipment id: {equipment_id}")
        return resolved
