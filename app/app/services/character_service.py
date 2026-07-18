from sqlalchemy.orm import Session

from app.models.character import Character, CharacterSkill, SavingThrowProficiency, AbilityName
from app.schemas.character import (
    CharacterCreate, CharacterUpdate, DerivedStats,
    SkillProficiencyIn, SavingThrowProficiencyIn,
)
from app.services.rules import ability_scores, proficiency, hit_points, initiative, armor, skills as skills_rules


def compute_derived_stats(character: Character) -> DerivedStats:
    """Single entry point for all derived stats. UI/API never calculate these themselves."""
    mods = ability_scores.all_modifiers(character)
    prof = proficiency.proficiency_bonus(character.level)
    skill_values = skills_rules.all_skill_values(character, prof)
    saving_throws = ability_scores.all_saving_throws(character, prof)

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
        armor_class=armor.armor_class(character.dexterity),
        passive_perception=skills_rules.passive_score(skill_values["perception"]),
        skills=skill_values,
        saving_throws=saving_throws,
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
