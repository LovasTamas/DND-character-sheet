import json

from sheet_project.engine.classes.proficiencies import ARMORPROF
from sheet_project.engine.equipment.armor import Armor
from sheet_project.engine.paths import DATA_DIR


class ArmorLoader:
    def __init__(self, needed_ids: list[str]):
        self.path_to_data = DATA_DIR / "armors.json"
        self.needed_ids = needed_ids

    def load(self) -> dict[str, Armor]:
        with open(self.path_to_data, "r", encoding="utf-8") as f:
            raw = json.load(f)["armors"]
        return {i: self._build_armor(raw[i]) for i in self.needed_ids}

    @staticmethod
    def _build_armor(data: dict) -> Armor:
        return Armor(
            data["id"],
            data["name"],
            ARMORPROF(data["category"]),
            data["base_ac"],
            data["ac_bonus"],
            data["dex_bonus"],
            data["strength_requirement"],
            data["stealth_disadvantage"],
            data["weight"],
            data["cost"],
        )

    @classmethod
    def list_armors(cls) -> list[dict]:
        with open(DATA_DIR / "armors.json", "r", encoding="utf-8") as f:
            raw = json.load(f)["armors"]
            return [
                {"id": aid, "name": a["name"], "category": a["category"]}
                for aid, a in raw.items()
            ]
