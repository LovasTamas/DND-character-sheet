from enum import Enum

class ATTRIBUTE(Enum):
    STRENGTH: 1
    DEXTERITY: 2
    CONSTITUTION: 3
    INTELLIGENCE: 4
    WISDOM: 5
    CHARISMA: 6

class CharacterAttributes:
    def __init__(self):
        self.attributes = {}
        self.modifiers = {}
        for i in ATTRIBUTE:
            self.attributes[i] = 0
            self.modifiers[i] = -5
    
    def update_attribute(self, type: ATTRIBUTE, value):
        self.attributes[type] = value
        self.calculate_modifier(type)
    
    def get_attribute(self, type: ATTRIBUTE):
        return self.attributes[type]

    def calculate_modifier(self, type: ATTRIBUTE):
        self.modifiers[type] = int((self.attributes[type]-10)/2)
        pass