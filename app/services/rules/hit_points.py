from app.services.rules.ability_scores import modifier

# Placeholder until classes.json (hit die per class) lands in Phase 3.
DEFAULT_HIT_DIE = 8


def max_hp_level_1(constitution_score: int, hit_die: int = DEFAULT_HIT_DIE) -> int:
    return hit_die + modifier(constitution_score)
