from app.services.rules.ability_scores import modifier

UNARMORED_BASE = 10


def armor_class(dexterity_score: int, armor_bonus: int = 0) -> int:
    """Unarmored baseline only. Real armor/shield stacking rules land in Phase 4."""
    return UNARMORED_BASE + modifier(dexterity_score) + armor_bonus
