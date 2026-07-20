import json

from sheet_project.engine.classes.proficiencies import WEPPROF
from sheet_project.engine.equipment.weapon import Weapon
from sheet_project.engine.paths import DATA_DIR


class WeaponLoader:
    def __init__(self, needed_ids: list[str]):
        self.path_to_data = DATA_DIR / "weapons.json"
        self.needed_ids = needed_ids

    def load(self) -> dict[str, Weapon]:
        with open(self.path_to_data, "r", encoding="utf-8") as f:
            raw = json.load(f)["weapons"]
        return {i: self._build_weapon(raw[i]) for i in self.needed_ids}

    @staticmethod
    def _build_weapon(data: dict) -> Weapon:
        return Weapon(
            data["id"],
            data["name"],
            WEPPROF(data["category"]),
            data["type"],
            data["damage"],
            data["versatile_damage"],
            frozenset(data["properties"]),
            data["mastery"],
            data["range"],
            data["weight"],
            data["cost"],
        )
