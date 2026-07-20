from sheet_project.engine.character import Character
from sheet_project.engine.classes.character_class import CharacterClass
from sheet_project.engine.classes.class_loader import ClassLoader
from sheet_project.engine.classes.proficiencies import SKILLPROF


my_char = Character("Tomi", "figHTer")
my_char.set_hp(3)
for i in my_char.ability_points.keys():
    my_char.set_ability(i, 11)
my_char.add_skill_prof(SKILLPROF.ACROBATICS)
print(my_char.max_hp)
print(my_char.proficiency_bonus)
print(my_char.skills)
print(my_char.skill_profs)