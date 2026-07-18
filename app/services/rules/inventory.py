from app.services import data_loader

CAPACITY_PER_STRENGTH = 15  # PHB 2024: carrying capacity = Strength score x 15
ENCUMBERED_SPEED_PENALTY = 10


def carrying_capacity(strength_score: int) -> int:
    return strength_score * CAPACITY_PER_STRENGTH


def total_weight(character) -> float:
    weight = 0.0
    for item in character.inventory_items:
        weight += data_loader.get_item_weight(item.item_key) * item.quantity
    return weight


def encumbrance_status(character) -> dict:
    capacity = carrying_capacity(character.strength)
    weight = total_weight(character)
    encumbered = weight > capacity
    return {
        "total_weight": weight,
        "capacity": capacity,
        "encumbered": encumbered,
        "speed_penalty": ENCUMBERED_SPEED_PENALTY if encumbered else 0,
    }
