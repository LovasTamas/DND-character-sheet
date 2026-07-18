from attributes import ATTRIBUTE, CharacterAttributes
from modifiers import MODIFIERS, CharacterModifiers
from race import Race

class Character:
    def __init__(self):
        self.class_ = None
        self.level = 1
        self.modifiers = CharacterModifiers()
        self.ac = 0
        self.attributes = CharacterAttributes()
        self.race = None
        self.spells = None
        self.inventory = None
        pass

    def set_race(self, race: Race):
        self.race = race
    
    def set_class(self, class_):
        self.class_ = class_

    def update_level(self, value):
        self.level = value
