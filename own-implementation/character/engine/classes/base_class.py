from abc import ABC, abstractmethod
from proficiencies import SKILLPROFICIENCY, ARMORTRAINING, WEAPONTRAINING
from attributes import ATTRIBUTE

class BaseClass(ABC):
    def __init__(self):
        super().__init__()
        self.skill_prof = {}
        self.armor_training = {}
        self.weapon_training = {}
        self.saving_throw = {}
        for i in SKILLPROFICIENCY:
            self.skill_prof[i] = False
        for i in ARMORTRAINING:
            self.armor_training[i] = False
        for i in WEAPONTRAINING:
            self.weapon_training[i] = False
        for i in ATTRIBUTE:
            self.saving_throw[i] = False

    @abstractmethod
    def select_skill_prof(self, type: SKILLPROFICIENCY):
        self.skill_prof[type] = True

    @abstractmethod
    def select_armor_training(self, type: ARMORTRAINING):
        self.armor_training[type] = True

    @abstractmethod
    def select_weapon_training(self, type: WEAPONTRAINING):
        self.weapon_training[type] = True
    
    @abstractmethod
    def select_saving_throw(self, type: ATTRIBUTE):
        self.saving_throw[type] = True