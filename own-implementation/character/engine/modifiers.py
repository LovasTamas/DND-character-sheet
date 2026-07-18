from enum import Enum

class MODIFIERS(Enum):
    HP_MODIFIER = 1


class CharacterModifiers:
    def __init__(self):
        self.modifiers = {}
        for i in MODIFIERS:
            self.modifiers[i] = 0