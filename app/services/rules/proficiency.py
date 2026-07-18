def proficiency_bonus(level: int) -> int:
    if level < 1 or level > 20:
        raise ValueError("level must be between 1 and 20")
    return 2 + (level - 1) // 4
