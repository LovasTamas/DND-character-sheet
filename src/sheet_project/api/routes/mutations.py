"""Character mutation endpoints, all under `/characters/{character_id}`.

Per docs/webui-architecture.md#Character-mutations. Every handler:
load -> mutate via a single engine call (validating first so the
engine's silent no-ops become proper 4xx responses) -> save -> return
the fresh `{id, ...to_dict()}` body.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query, status

from sheet_project.engine.character import Character
from sheet_project.engine.backgrounds.background_loader import BackgroundLoader
from sheet_project.engine.classes.abilities import ABILITIES
from sheet_project.engine.classes.class_loader import ClassLoader
from sheet_project.engine.classes.proficiencies import ARMORPROF, SKILLPROF
from sheet_project.engine.features.active_feature import ActiveFeature
from sheet_project.engine.features.choice_feature import ChoiceFeature
from sheet_project.engine.races.race_loader import RaceLoader
from sheet_project.engine.rest_type import RESTTYPE
from sheet_project.engine.subclasses.subclass_loader import SubclassLoader

from .. import deps
from ..errors import ApiError, bad_request, conflict, not_found
from ..schemas import (
    AbilityScoreUpdate,
    AmountRequest,
    BackgroundAbilityBonusesUpdate,
    BackgroundUpdate,
    ChoiceUpdate,
    ClassUpdate,
    EquipArmorRequest,
    EquipShieldRequest,
    EquipWeaponRequest,
    HpUpdate,
    InventoryAddRequest,
    LevelUpdate,
    NameUpdate,
    RaceUpdate,
    SkillProfUpdate,
    SubclassUpdate,
    TemporaryHpUpdate,
)

router = APIRouter(prefix="/characters/{character_id}", tags=["mutations"])


def _known_ids(items) -> set:
    return {item["id"] for item in items}


def _finish(character_id: str, character: Character) -> dict:
    deps.save_character(character_id, character)
    return deps.character_response(character_id, character)


def _ability_or_404(ability: str) -> ABILITIES:
    try:
        return ABILITIES(ability)
    except ValueError as exc:
        raise not_found(f"Unknown ability '{ability}'", code="unknown_ability", field="ability") from exc


def _skill_or_404(skill: str) -> SKILLPROF:
    try:
        return SKILLPROF(skill)
    except ValueError as exc:
        raise not_found(f"Unknown skill '{skill}'", code="unknown_skill", field="skill") from exc


def _inventory_item(character: Character, item_id: str):
    for entry in character.inventory:
        if entry.item.id == item_id:
            return entry.item
    return None


@router.patch("/name")
def update_name(character_id: str, body: NameUpdate) -> dict:
    character = deps.load_character(character_id)
    character.set_name(body.name)
    return _finish(character_id, character)


@router.patch("/class")
def update_class(character_id: str, body: ClassUpdate) -> dict:
    character = deps.load_character(character_id)
    if body.class_name.lower() not in _known_ids(ClassLoader.list_classes()):
        raise not_found(f"Unknown class '{body.class_name}'", code="unknown_class", field="class_name")
    character.set_class(body.class_name)
    return _finish(character_id, character)


@router.patch("/race")
def update_race(character_id: str, body: RaceUpdate) -> dict:
    character = deps.load_character(character_id)
    if body.race_name is not None and body.race_name.lower() not in _known_ids(RaceLoader.list_races()):
        raise not_found(f"Unknown race '{body.race_name}'", code="unknown_race", field="race_name")
    character.set_race(body.race_name)
    return _finish(character_id, character)


@router.patch("/background")
def update_background(character_id: str, body: BackgroundUpdate) -> dict:
    character = deps.load_character(character_id)
    if body.background_name is not None and body.background_name.lower() not in _known_ids(
        BackgroundLoader.list_backgrounds()
    ):
        raise not_found(
            f"Unknown background '{body.background_name}'",
            code="unknown_background",
            field="background_name",
        )
    character.set_background(body.background_name)
    return _finish(character_id, character)


@router.patch("/subclass")
def update_subclass(character_id: str, body: SubclassUpdate) -> dict:
    character = deps.load_character(character_id)
    ok = character.set_subclass(body.subclass_id)
    if not ok:
        raise bad_request(
            "Invalid subclass id, or character level too low to unlock a subclass.",
            code="invalid_subclass",
            field="subclass_id",
        )
    return _finish(character_id, character)


@router.patch("/level")
def update_level(character_id: str, body: LevelUpdate) -> dict:
    if body.level < 1 or body.level > 20:
        raise bad_request("Level must be between 1 and 20.", code="invalid_level", field="level")
    character = deps.load_character(character_id)
    character.level_up(body.level)
    return _finish(character_id, character)


@router.patch("/ability/{ability}")
def update_ability(character_id: str, ability: str, body: AbilityScoreUpdate) -> dict:
    ability_enum = _ability_or_404(ability)
    if body.value < 0 or body.value > 20:
        raise bad_request(
            "Ability score must be between 0 and 20.", code="invalid_ability_score", field="value"
        )
    character = deps.load_character(character_id)
    character.set_ability(ability_enum, body.value)
    return _finish(character_id, character)


@router.patch("/background-ability-bonuses")
def update_background_ability_bonuses(character_id: str, body: BackgroundAbilityBonusesUpdate) -> dict:
    character = deps.load_character(character_id)
    try:
        bonuses = {ABILITIES(key): value for key, value in body.items()}
    except ValueError as exc:
        raise bad_request(f"Unknown ability in bonuses: {exc}", code="unknown_ability") from exc

    ok = character.set_background_ability_bonuses(bonuses)
    if not ok:
        raise bad_request(
            "Invalid ability bonus distribution for this background.",
            code="invalid_ability_distribution",
        )
    return _finish(character_id, character)


@router.patch("/skill/{skill}")
def update_skill(character_id: str, skill: str, body: SkillProfUpdate) -> dict:
    skill_enum = _skill_or_404(skill)
    character = deps.load_character(character_id)
    if body.proficient:
        character.add_skill_prof(skill_enum)
    else:
        character.remove_skill_prof(skill_enum)
    return _finish(character_id, character)


@router.patch("/hp")
def update_hp(character_id: str, body: HpUpdate) -> dict:
    character = deps.load_character(character_id)
    # Vision: "Clamped [0, max_hp] on send" - clamp server-side too, since
    # `set_hp` silently no-ops on out-of-range values instead of clamping.
    clamped = max(0, min(body.value, character.max_hp))
    character.set_hp(clamped)
    return _finish(character_id, character)


@router.patch("/temporary-hp")
def update_temporary_hp(character_id: str, body: TemporaryHpUpdate) -> dict:
    character = deps.load_character(character_id)
    character.set_temporary_hp(body.value)
    return _finish(character_id, character)


@router.post("/damage")
def post_damage(character_id: str, body: AmountRequest) -> dict:
    if body.amount < 0:
        raise bad_request("Damage amount must be >= 0.", code="invalid_amount", field="amount")
    character = deps.load_character(character_id)
    character.take_damage(body.amount)
    return _finish(character_id, character)


@router.post("/heal")
def post_heal(character_id: str, body: AmountRequest) -> dict:
    if body.amount < 0:
        raise bad_request("Heal amount must be >= 0.", code="invalid_amount", field="amount")
    character = deps.load_character(character_id)
    character.heal(body.amount)
    return _finish(character_id, character)


@router.post("/hit-dice/spend")
def post_spend_hit_die(character_id: str) -> dict:
    character = deps.load_character(character_id)
    die = character.spend_hit_die()
    if die is None:
        raise bad_request("No hit dice remaining.", code="no_hit_dice")
    deps.save_character(character_id, character)
    return {
        "die": die,
        "remaining": character.hit_dice_remaining,
        "character": deps.character_response(character_id, character),
    }


@router.post("/rest/short")
def post_rest_short(character_id: str) -> dict:
    character = deps.load_character(character_id)
    character.rest(RESTTYPE.SHORT)
    return _finish(character_id, character)


@router.post("/rest/long")
def post_rest_long(character_id: str) -> dict:
    character = deps.load_character(character_id)
    character.rest(RESTTYPE.LONG)
    return _finish(character_id, character)


@router.post("/feature/{feature_id}/use")
def post_use_feature(character_id: str, feature_id: str) -> dict:
    character = deps.load_character(character_id)
    feature = character.features.get(feature_id)
    if feature is None:
        raise not_found(f"Unknown feature '{feature_id}'", code="unknown_feature", field="feature_id")
    ok = character.use_feature(feature_id)
    if not ok:
        raise bad_request(
            f"Feature '{feature_id}' is not usable right now.",
            code="feature_not_usable",
            field="feature_id",
        )
    return _finish(character_id, character)


@router.patch("/choice/{feature_id}")
def patch_choice(character_id: str, feature_id: str, body: ChoiceUpdate) -> dict:
    character = deps.load_character(character_id)
    feature = character.features.get(feature_id)
    if feature is None:
        raise not_found(f"Unknown feature '{feature_id}'", code="unknown_feature", field="feature_id")
    if not isinstance(feature, ChoiceFeature):
        raise bad_request(
            f"Feature '{feature_id}' does not accept a choice.",
            code="not_a_choice_feature",
            field="feature_id",
        )
    feature.choose(character, body.value)
    return _finish(character_id, character)


@router.post("/inventory", status_code=status.HTTP_200_OK)
def post_inventory(character_id: str, body: InventoryAddRequest) -> dict:
    if body.quantity < 1:
        raise bad_request("Quantity must be >= 1.", code="invalid_quantity", field="quantity")
    character = deps.load_character(character_id)
    try:
        character.add_item(body.item_id, body.quantity)
    except KeyError as exc:
        raise not_found(f"Unknown item '{body.item_id}'", code="unknown_item", field="item_id") from exc
    return _finish(character_id, character)


@router.delete("/inventory/{item_id}")
def delete_inventory(character_id: str, item_id: str, quantity: int = Query(1, ge=1)) -> dict:
    character = deps.load_character(character_id)
    if _inventory_item(character, item_id) is None:
        raise conflict(
            f"Item '{item_id}' is not in the inventory.", code="item_not_in_inventory", field="item_id"
        )
    character.remove_item(item_id, quantity)
    return _finish(character_id, character)


@router.post("/equipped/weapons")
def post_equip_weapon(character_id: str, body: EquipWeaponRequest) -> dict:
    character = deps.load_character(character_id)
    if _inventory_item(character, body.weapon_id) is None:
        raise conflict(
            f"Weapon '{body.weapon_id}' is not in the inventory.",
            code="item_not_in_inventory",
            field="weapon_id",
        )
    character.equip_weapon(body.weapon_id)
    return _finish(character_id, character)


@router.delete("/equipped/weapons/{weapon_id}")
def delete_equip_weapon(character_id: str, weapon_id: str) -> dict:
    character = deps.load_character(character_id)
    if not any(w.id == weapon_id for w in character.equipped_weapons):
        raise conflict(
            f"Weapon '{weapon_id}' is not currently equipped.",
            code="item_not_equipped",
            field="weapon_id",
        )
    character.unequip_weapon(weapon_id)
    return _finish(character_id, character)


@router.put("/equipped/armor")
def put_equip_armor(character_id: str, body: EquipArmorRequest) -> dict:
    character = deps.load_character(character_id)
    if body.armor_id is None:
        character.unequip_armor()
        return _finish(character_id, character)

    item = _inventory_item(character, body.armor_id)
    if item is None:
        raise conflict(
            f"Armor '{body.armor_id}' is not in the inventory.", code="item_not_in_inventory", field="armor_id"
        )
    if getattr(item, "category", None) not in (ARMORPROF.LIGHT, ARMORPROF.MEDIUM, ARMORPROF.HEAVY):
        raise conflict(
            f"Item '{body.armor_id}' is not body armor.", code="wrong_equipment_slot", field="armor_id"
        )
    character.equip_armor(body.armor_id)
    return _finish(character_id, character)


@router.put("/equipped/shield")
def put_equip_shield(character_id: str, body: EquipShieldRequest) -> dict:
    character = deps.load_character(character_id)
    if body.shield_id is None:
        character.unequip_shield()
        return _finish(character_id, character)

    item = _inventory_item(character, body.shield_id)
    if item is None:
        raise conflict(
            f"Shield '{body.shield_id}' is not in the inventory.",
            code="item_not_in_inventory",
            field="shield_id",
        )
    if getattr(item, "category", None) != ARMORPROF.SHIELD:
        raise conflict(
            f"Item '{body.shield_id}' is not a shield.", code="wrong_equipment_slot", field="shield_id"
        )
    character.equip_shield(body.shield_id)
    return _finish(character_id, character)
