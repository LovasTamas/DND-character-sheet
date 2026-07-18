from race import Race
from character import Character
from traits.dwarf_traits import Stonecunning, Dwarven_Resilience, Dwarven_Toughness, Darkvision

class Dwarf(Race):
    def __init__(self, character: Character):
        super().__init__("Dwarf")
        self.features = [Stonecunning(character), Dwarven_Resilience(), Dwarven_Toughness(character), Darkvision()]
        self.speed = 30
        self.size = "M"
        
