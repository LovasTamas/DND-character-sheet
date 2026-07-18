from app.services.rules.ability_scores import modifier
from app.services import data_loader

UNARMORED_BASE = 10


def _equipped(character, item_type: str):
    return next(
        (i for i in character.inventory_items if i.item_type == item_type and i.equipped),
        None,
    )


def armor_class(character, temp_bonus: int = 0) -> int:
    """Full PHB 2024 AC stacking: at most one body armor + optionally one shield."""
    dex_mod = modifier(character.dexterity)

    armor_item = _equipped(character, "armor")
    if armor_item is None:
        ac = UNARMORED_BASE + dex_mod
    else:
        data = data_loader.get_armor(armor_item.item_key)
        if data is None:
            raise ValueError(f"Unknown armor item_key: {armor_item.item_key}")

        category = data["category"]
        if category == "light":
            ac = data["base_ac"] + dex_mod
        elif category == "medium":
            ac = data["base_ac"] + min(dex_mod, data["dex_cap"])
        elif category == "heavy":
            ac = data["base_ac"]
        else:
            raise ValueError(f"Armor {armor_item.item_key} has non-body category: {category}")

        ac += armor_item.magic_bonus

    shield_item = _equipped(character, "shield")
    if shield_item is not None:
        shield_data = data_loader.get_armor(shield_item.item_key)
        ac += shield_data["ac_bonus"] + shield_item.magic_bonus

    return ac + temp_bonus


def meets_str_requirement(character, armor_key: str) -> bool:
    data = data_loader.get_armor(armor_key)
    requirement = data.get("str_requirement") if data else None
    return requirement is None or character.strength >= requirement


def imposes_stealth_disadvantage(character) -> bool:
    armor_item = _equipped(character, "armor")
    if armor_item is None:
        return False
    data = data_loader.get_armor(armor_item.item_key)
    return bool(data and data.get("stealth_disadvantage"))
