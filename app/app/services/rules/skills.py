from app.services.rules.ability_scores import modifier

# PHB 2024 skill -> governing ability
SKILL_ABILITY_MAP = {
    "acrobatics": "dexterity",
    "animal_handling": "wisdom",
    "arcana": "intelligence",
    "athletics": "strength",
    "deception": "charisma",
    "history": "intelligence",
    "insight": "wisdom",
    "intimidation": "charisma",
    "investigation": "intelligence",
    "medicine": "wisdom",
    "nature": "intelligence",
    "perception": "wisdom",
    "performance": "charisma",
    "persuasion": "charisma",
    "religion": "intelligence",
    "sleight_of_hand": "dexterity",
    "stealth": "dexterity",
    "survival": "wisdom",
}


def skill_value(
    skill_name: str,
    ability_score: int,
    proficiency_bonus: int,
    proficient: bool = False,
    expertise: bool = False,
    temp_bonus: int = 0,
) -> int:
    if skill_name not in SKILL_ABILITY_MAP:
        raise ValueError(f"Unknown skill: {skill_name}")

    bonus = 0
    if expertise:
        bonus = proficiency_bonus * 2
    elif proficient:
        bonus = proficiency_bonus

    return modifier(ability_score) + bonus + temp_bonus


def all_skill_values(character, proficiency_bonus: int) -> dict[str, int]:
    """Compute every skill for a character, using its stored proficiency/expertise rows.
    Skills with no CharacterSkill row default to unproficient, no temp bonus.
    """
    overrides = {s.skill_name: s for s in character.skills}

    results = {}
    for skill_name, ability in SKILL_ABILITY_MAP.items():
        row = overrides.get(skill_name)
        proficient = row.proficient if row else False
        expertise = row.expertise if row else False
        temp_bonus = row.temp_bonus if row else 0

        ability_score = getattr(character, ability)
        results[skill_name] = skill_value(
            skill_name, ability_score, proficiency_bonus,
            proficient=proficient, expertise=expertise, temp_bonus=temp_bonus,
        )
    return results


def passive_score(skill_value_: int) -> int:
    return 10 + skill_value_
