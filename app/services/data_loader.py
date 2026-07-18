import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


@lru_cache
def _load(filename: str) -> dict:
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def load_armor() -> dict:
    return _load("armor.json")


def load_weapons() -> dict:
    return _load("weapons.json")


def load_equipment() -> dict:
    return _load("equipment.json")


def get_armor(key: str) -> dict | None:
    return load_armor().get(key)


def get_weapon(key: str) -> dict | None:
    return load_weapons().get(key)


def get_equipment(key: str) -> dict | None:
    return load_equipment().get(key)


def get_item_weight(item_key: str) -> float:
    """Look up an item's weight across all three data packages, in gear -> weapon -> armor order."""
    for loader in (load_equipment, load_weapons, load_armor):
        item = loader().get(item_key)
        if item is not None:
            return item.get("weight_lb", 0)
    raise KeyError(f"Unknown item: {item_key}")
