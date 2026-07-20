import json

from sheet_project.engine.equipment.item import Item
from sheet_project.engine.paths import DATA_DIR


class ItemLoader:
    def __init__(self, needed_ids: list[str]):
        self.path_to_data = DATA_DIR / "items.json"
        self.needed_ids = needed_ids

    def load(self) -> dict[str, Item]:
        with open(self.path_to_data, "r", encoding="utf-8") as f:
            raw = json.load(f)["items"]
        return {i: self._build_item(raw[i]) for i in self.needed_ids}

    @staticmethod
    def _build_item(data: dict) -> Item:
        return Item(
            data["id"],
            data["name"],
            data["kind"],
            data["weight"],
            data["cost"],
        )

    @classmethod
    def list_items(cls) -> list[dict]:
        with open(DATA_DIR / "items.json", "r", encoding="utf-8") as f:
            raw = json.load(f)["items"]
            return [{"id": iid, "name": i["name"], "kind": i["kind"]} for iid, i in raw.items()]
