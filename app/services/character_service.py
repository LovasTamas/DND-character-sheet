from sqlalchemy.orm import Session

from app.models.character import Character, CharacterSkill, SavingThrowProficiency, InventoryItem, AbilityName, ItemType
from app.schemas.character import (
    CharacterCreate, CharacterUpdate, DerivedStats,
    SkillProficiencyIn, SavingThrowProficiencyIn, InventoryItemIn, CurrencyUpdate,
)
from app.services.rules import (
    ability_scores, proficiency, hit_points, initiative, armor, inventory as inventory_rules,
    skills as skills_rules,
)
from app.services import data_loader


def compute_derived_stats(character: Character) -> DerivedStats:
    """Single entry point for all derived stats. UI/API never calculate these themselves."""
    mods = ability_scores.all_modifiers(character)
    prof = proficiency.proficiency_bonus(character.level)
    skill_values = skills_rules.all_skill_values(character, prof)
    saving_throws = ability_scores.all_saving_throws(character, prof)
    encumbrance = inventory_rules.encumbrance_status(character)

    max_hp = (
        character.max_hp_override
        if character.max_hp_override is not None
        else hit_points.max_hp_level_1(character.constitution)
    )

    return DerivedStats(
        ability_modifiers=mods,
        proficiency_bonus=prof,
        max_hp=max_hp,
        initiative=initiative.initiative(character.dexterity),
        armor_class=armor.armor_class(character),
        passive_perception=skills_rules.passive_score(skill_values["perception"]),
        skills=skill_values,
        saving_throws=saving_throws,
        carrying_capacity=encumbrance["capacity"],
        total_weight=encumbrance["total_weight"],
        encumbered=encumbrance["encumbered"],
        speed_penalty=encumbrance["speed_penalty"],
    )


def create_character(db: Session, data: CharacterCreate) -> Character:
    character = Character(
        name=data.name,
        level=data.level,
        species=data.species,
        class_name=data.class_name,
        subclass=data.subclass,
        background=data.background,
        alignment=data.alignment,
        strength=data.abilities.strength,
        dexterity=data.abilities.dexterity,
        constitution=data.abilities.constitution,
        intelligence=data.abilities.intelligence,
        wisdom=data.abilities.wisdom,
        charisma=data.abilities.charisma,
    )
    character.current_hp = hit_points.max_hp_level_1(character.constitution)
    db.add(character)
    db.commit()
    db.refresh(character)
    return character


def get_character(db: Session, character_id: int) -> Character | None:
    return db.get(Character, character_id)


def list_characters(db: Session) -> list[Character]:
    return db.query(Character).all()


def update_character(db: Session, character: Character, data: CharacterUpdate) -> Character:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(character, field, value)
    db.commit()
    db.refresh(character)
    return character


def delete_character(db: Session, character: Character) -> None:
    db.delete(character)
    db.commit()


def set_skill_proficiency(db: Session, character: Character, data: SkillProficiencyIn) -> Character:
    if data.skill_name not in skills_rules.SKILL_ABILITY_MAP:
        raise ValueError(f"Unknown skill: {data.skill_name}")

    row = next((s for s in character.skills if s.skill_name == data.skill_name), None)
    if row is None:
        row = CharacterSkill(character_id=character.id, skill_name=data.skill_name)
        db.add(row)

    row.proficient = data.proficient
    row.expertise = data.expertise
    row.temp_bonus = data.temp_bonus
    db.commit()
    db.refresh(character)
    return character


def set_saving_throw_proficiency(db: Session, character: Character, data: SavingThrowProficiencyIn) -> Character:
    try:
        ability = AbilityName(data.ability)
    except ValueError:
        raise ValueError(f"Unknown ability: {data.ability}")

    exists = any(stp.ability == ability for stp in character.saving_throw_proficiencies)
    if not exists:
        db.add(SavingThrowProficiency(character_id=character.id, ability=ability))
        db.commit()
        db.refresh(character)
    return character


def add_inventory_item(db: Session, character: Character, data: InventoryItemIn) -> Character:
    try:
        item_type = ItemType(data.item_type)
    except ValueError:
        raise ValueError(f"Unknown item_type: {data.item_type}")

    lookup = {
        ItemType.weapon: data_loader.get_weapon,
        ItemType.armor: data_loader.get_armor,
        ItemType.shield: data_loader.get_armor,
        ItemType.gear: data_loader.get_equipment,
    }[item_type]
    if lookup(data.item_key) is None:
        raise ValueError(f"Unknown {item_type.value} item_key: {data.item_key}")

    if data.equipped and item_type == ItemType.armor:
        # Only one body armor may be equipped at a time.
        for existing in character.inventory_items:
            if existing.item_type == ItemType.armor and existing.equipped:
                existing.equipped = False

    item = InventoryItem(
        character_id=character.id,
        item_key=data.item_key,
        item_type=item_type,
        quantity=data.quantity,
        equipped=data.equipped,
        attuned=data.attuned,
        magic_bonus=data.magic_bonus,
    )
    db.add(item)
    db.commit()
    db.refresh(character)
    return character


def remove_inventory_item(db: Session, character: Character, item_id: int) -> Character:
    item = next((i for i in character.inventory_items if i.id == item_id), None)
    if item is None:
        raise ValueError(f"Inventory item {item_id} not found on this character")
    db.delete(item)
    db.commit()
    db.refresh(character)
    return character


def set_item_equipped(db: Session, character: Character, item_id: int, equipped: bool) -> Character:
    item = next((i for i in character.inventory_items if i.id == item_id), None)
    if item is None:
        raise ValueError(f"Inventory item {item_id} not found on this character")

    if equipped and item.item_type == ItemType.armor:
        for existing in character.inventory_items:
            if existing.item_type == ItemType.armor and existing.id != item.id:
                existing.equipped = False

    item.equipped = equipped
    db.commit()
    db.refresh(character)
    return character


def update_currency(db: Session, character: Character, data: CurrencyUpdate) -> Character:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(character, field, value)
    db.commit()
    db.refresh(character)
    return character
