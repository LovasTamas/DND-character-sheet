ABILITIES = [
    "strength", "dexterity", "constitution",
    "intelligence", "wisdom", "charisma",
]


def modifier(score: int) -> int:
    """Standard D&D modifier formula, floor division toward negative infinity."""
    return (score - 10) // 2


def all_modifiers(character) -> dict[str, int]:
    return {ability: modifier(getattr(character, ability)) for ability in ABILITIES}


def saving_throw(ability_score: int, proficiency_bonus: int, proficient: bool = False, temp_bonus: int = 0) -> int:
    return modifier(ability_score) + (proficiency_bonus if proficient else 0) + temp_bonus


def all_saving_throws(character, proficiency_bonus: int) -> dict[str, int]:
    proficient_abilities = {stp.ability.value for stp in character.saving_throw_proficiencies}
    return {
        ability: saving_throw(
            getattr(character, ability), proficiency_bonus,
            proficient=ability in proficient_abilities,
        )
        for ability in ABILITIES
    }
