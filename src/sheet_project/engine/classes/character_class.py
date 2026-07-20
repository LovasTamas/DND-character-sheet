from dataclasses import dataclass

from sheet_project.engine.classes.abilities import ABILITIES
from sheet_project.engine.classes.proficiencies import ARMORPROF, WEPPROF
from sheet_project.engine.classes.hitpoints import HitPointProgression
from sheet_project.engine.features.active_feature import ActiveFeature
from sheet_project.engine.features.choice_feature import ChoiceFeature
from sheet_project.engine.features.feature import Feature


@dataclass(frozen=True)
class CharacterClass:
    class_name: str

    hitpoints: HitPointProgression

    armor_profs: set[ARMORPROF]
    weapon_profs: set[WEPPROF]

    saving_throw_profs: set[ABILITIES]
    features: set[Feature|ActiveFeature|ChoiceFeature]


# from engine.classes.abilities import ABILITIES
# from engine.classes.proficiencies import ARMORPROF, WEPPROF, SKILLPROF


# class CharacterClass:
#     def __init__(self, class_name: str, base_hit_points: dict, hit_points_per_level: dict, armor_profs: dict, wep_profs: dict, saving_profs: dict = {}):
#         self.class_name = class_name
#         self.level = 1
#         self.prof_bonus = 0
#         self.hit_points = hit_points
#         self.ability_points = {}
#         self.ability_modifiers = {}
#         self.saving_throw_values = {}
#         for i in ABILITIES:
#             self.ability_points[i] = 0
#             self.ability_modifiers[i] = 0
#             self.saving_throw_values[i] = 0
#         self.saving_profs = saving_profs
#         self.calculate_ability_modifiers()
#         self.skill_profs = {}
#         for i in SKILLPROF:
#             self.skill_profs[i] = False
#         self.armor_profs = armor_profs
#         self.wep_profs = wep_profs


#     def update_automatic_values(self):
#         self.calculate_prof_bonus()
#         self.calculate_ability_modifiers()
#         self.calculate_saving_throw_values()

#     def calculate_ability_modifiers(self):
#         for i in self.ability_points.keys():
#             self.ability_modifiers[i] = int((self.ability_points[i]-10)/2)

#     def calculate_saving_throw_values(self):
#         for i in self.ability_modifiers.keys():
#             if self.saving_profs[i]:
#                 self.saving_throw_values[i] = self.prof_bonus + self.ability_modifiers[i]
#             else:
#                 self.saving_throw_values[i] = self.ability_modifiers[i]
    
#     def calculate_prof_bonus(self):
#         self.prof_bonus = 2+((self.level-1)%4)

#     def add_skill_prof(self, skill: SKILLPROF):
#         self.skill_profs[skill] = True
    
#     def remove_skill_prof(self, skill: SKILLPROF):
#         self.skill_profs[skill] = False