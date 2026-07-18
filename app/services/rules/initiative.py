from app.services.rules.ability_scores import modifier


def initiative(dexterity_score: int, temp_bonus: int = 0) -> int:
    return modifier(dexterity_score) + temp_bonus
