from sheet_project.engine.classes.abilities import ABILITIES
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

c = Character("Tomi", "fighter", background_name="guard", race_name="human")
c.set_background_ability_bonuses({ABILITIES.STRENGTH: 2, ABILITIES.WISDOM: 1})
for a in ABILITIES:
    c.set_ability(a, 10)

assert SKILLPROF.ATHLETICS in c.skill_profs
assert SKILLPROF.PERCEPTION in c.skill_profs
assert "alert" in c.features
assert c.initiative == c.ability_modifiers[ABILITIES.DEXTERITY] + c.proficiency_bonus
assert c.ability_modifiers[ABILITIES.STRENGTH] == 1
print("Guard/Alert/Human integration test passed")

c.set_ability(ABILITIES.DEXTERITY, 14)

# Naked: 10 + DEX mod
assert c.ac == 12

# Background auto-seeded spear and light_crossbow into inventory
inventory_ids = {entry.item.id for entry in c.inventory}
assert {"spear", "light_crossbow"}.issubset(inventory_ids)

c.add_item("chain_mail")
c.add_item("shield")
c.equip_armor("chain_mail")
c.equip_shield("shield")
assert c.ac == 18  # 16 (heavy, ignores DEX) + 2 (shield)

c.unequip_shield()
assert c.ac == 16

print("Inventory / AC integration test passed")

soldier = Character("Lae", "fighter", background_name="soldier", race_name="human")
soldier.set_background_ability_bonuses(
    {ABILITIES.STRENGTH: 2, ABILITIES.CONSTITUTION: 1}
)
for a in ABILITIES:
    soldier.set_ability(a, 10)
soldier.set_ability(ABILITIES.DEXTERITY, 12)

assert SKILLPROF.ATHLETICS in soldier.skill_profs
assert SKILLPROF.INTIMIDATION in soldier.skill_profs
assert "savage_attacker" in soldier.features
assert soldier.initiative == soldier.ability_modifiers[ABILITIES.DEXTERITY]

soldier_inventory_ids = {entry.item.id for entry in soldier.inventory}
assert {"spear", "shortbow", "20_arrows"}.issubset(soldier_inventory_ids)

print("Soldier/Savage Attacker/Human integration test passed")