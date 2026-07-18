from app.services.rules.ability_scores import modifier
from app.services import data_loader


def attack_ability(character, weapon_data: dict, is_ranged_attack: bool = False) -> str:
    """Determine which ability governs an attack with this weapon.

    Finesse weapons use the higher of Strength/Dexterity (melee or thrown).
    Otherwise ranged weapons use Dexterity, melee weapons use Strength.
    """
    properties = weapon_data.get("properties", [])
    category = weapon_data["category"]

    if "finesse" in properties:
        return "dexterity" if character.dexterity >= character.strength else "strength"

    if category.endswith("_ranged"):
        return "dexterity"

    return "strength"


def attack_bonus(
    character,
    weapon_key: str,
    proficient: bool = True,
    proficiency_bonus: int = 2,
    magic_bonus: int = 0,
    is_ranged_attack: bool = False,
) -> int:
    data = data_loader.get_weapon(weapon_key)
    if data is None:
        raise ValueError(f"Unknown weapon: {weapon_key}")

    ability = attack_ability(character, data, is_ranged_attack)
    ability_mod = modifier(getattr(character, ability))
    prof = proficiency_bonus if proficient else 0
    return ability_mod + prof + magic_bonus


def damage(
    character,
    weapon_key: str,
    magic_bonus: int = 0,
    use_versatile: bool = False,
) -> dict:
    """Returns dice notation + flat modifier + damage type. Dice are not rolled here —
    that's a presentation-layer concern; the engine only supplies the formula.
    """
    data = data_loader.get_weapon(weapon_key)
    if data is None:
        raise ValueError(f"Unknown weapon: {weapon_key}")

    properties = data.get("properties", [])
    ability = attack_ability(character, data)
    ability_mod = modifier(getattr(character, ability))

    dice = data["damage_dice"]
    if use_versatile:
        if "versatile" not in properties:
            raise ValueError(f"{weapon_key} does not have the versatile property")
        dice = data["versatile_dice"]

    return {
        "dice": dice,
        "modifier": ability_mod + magic_bonus,
        "damage_type": data["damage_type"],
        "mastery": data.get("mastery"),
    }


def has_property(weapon_key: str, property_name: str) -> bool:
    data = data_loader.get_weapon(weapon_key)
    return bool(data and property_name in data.get("properties", []))
