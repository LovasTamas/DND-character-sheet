from trait import Trait
from character import Character
from modifiers import MODIFIERS

class Stonecunning(Trait):
    def __init__(self, character: Character):
        super().__init__("Stonecunning", 
                         """As a Bonus Action, you gain Tremorsense with a range of 60 feet for 10 minutes. You must be on a stone surface or touching a stone surface to use this Tremorsense.
                         The stone can be natural or worked.You can use this Bonus Action a number of times equal to your Proficiency Bonus, and you regain all expended uses when you finish a Long Rest.""")
        self.max_uses = character.get_prof_bonus()
        self.usage = 0

    def level_up(self, character: Character):
        self.max_uses = character.get_prof_bonus()

    def use_trait(self):
        if self.max_uses - self.usage > 0:
            self.usage += 1
    
    def long_rest(self):
        self.usage = self.max_uses

class Dwarven_Toughness(Trait):
    def __init__(self, character: Character):
        super().__init__("Dwarven Toughness",
                         """Your Hit Point maximum increases by 1, and it increases by 1 again whenever you gain a level.""")
        self.modifier = character.level

    def get_modifier(self):
        return self.modifier
    
    def level_up(self, character: Character):
        self.modifier = character.level
    
class Darkvision(Trait):
    def __init__(self):
        super().__init__("Darkvision", """You have Darkvision with a range of 120 feet.""")

class Dwarven_Resilience(Trait):
    def __init__(self):
        super().__init__("Dwarven Resilience", """You have Resistance to Poison damage. You also have Advantage on saving throws you make to avoid or end the Poisoned condition.""")