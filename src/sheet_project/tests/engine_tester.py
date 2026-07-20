import json
import os
import tempfile

from sheet_project.engine.classes.abilities import ABILITIES
from sheet_project.engine.character import Character
from sheet_project.engine.classes.character_class import CharacterClass
from sheet_project.engine.classes.class_loader import ClassLoader
from sheet_project.engine.classes.proficiencies import SKILLPROF
from sheet_project.engine.backgrounds.background_loader import BackgroundLoader
from sheet_project.engine.races.race_loader import RaceLoader
from sheet_project.engine.features.feat_loader import FeatLoader
from sheet_project.engine.equipment.weapon_loader import WeaponLoader
from sheet_project.engine.equipment.armor_loader import ArmorLoader
from sheet_project.engine.equipment.item_loader import ItemLoader
from sheet_project.engine.rest_type import RESTTYPE
from sheet_project.engine import persistence


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

# --- §1 Catalog listing helpers ---

assert {"id": "fighter", "name": "Fighter"} in ClassLoader.list_classes()
assert {"id": "guard", "name": "Guard"} in BackgroundLoader.list_backgrounds()
assert {"id": "human", "name": "Human"} in RaceLoader.list_races()
assert {"id": "alert", "name": "Alert"} in FeatLoader.list_feats()
assert any(w["id"] == "spear" for w in WeaponLoader.list_weapons())
assert any(a["id"] == "chain_mail" for a in ArmorLoader.list_armors())
assert any(i["id"] == "backpack" for i in ItemLoader.list_items())

print("Catalog listing helpers test passed")

# --- §4 Temporary HP ---

temp_char = Character("Temp", "fighter")
for a in ABILITIES:
    temp_char.set_ability(a, 14)
temp_char.set_hp(temp_char.max_hp)

temp_char.set_temporary_hp(5)
temp_char.take_damage(3)
assert temp_char.temporary_hp == 2
assert temp_char.current_hp == temp_char.max_hp

temp_char.take_damage(8)
assert temp_char.temporary_hp == 0
assert temp_char.current_hp == temp_char.max_hp - 6

print("Temporary HP test passed")

# --- §5 Hit dice ---

hd_char = Character("HitDice", "fighter")
hd_char.level_up(5)
assert hd_char.hit_dice_total == 5
assert hd_char.hit_dice_remaining == 5

die = hd_char.spend_hit_die()
assert die == "d10"
assert hd_char.hit_dice_remaining == 4

hd_char.rest(RESTTYPE.LONG)
assert hd_char.hit_dice_remaining == 5
assert hd_char.temporary_hp == 0
assert hd_char.current_hp == hd_char.max_hp

print("Hit dice test passed")

# --- §3 Setters ---

setter_char = Character("Setter", "fighter", background_name="guard", race_name="human")
setter_char.set_name("Renamed")
assert setter_char.name == "Renamed"

setter_char.set_class("fighter")  # only fighter is modeled today; re-load is still a valid check
assert setter_char.character_class.class_name == "fighter"

setter_char.set_race(None)
assert setter_char.race is None
assert setter_char.speed == 30

before_inventory = {entry.item.id for entry in setter_char.inventory}
setter_char.set_background("soldier")
after_inventory = {entry.item.id for entry in setter_char.inventory}
assert "alert" not in setter_char.features
assert "savage_attacker" in setter_char.features
# Additive-with-dedupe: previously seeded ids survive, new ones are added.
assert before_inventory.issubset(after_inventory)
assert {"shortbow", "20_arrows"}.issubset(after_inventory)

setter_char.set_background(None)
assert setter_char.background is None
assert setter_char.tool_profs == set()

print("Setters test passed")

# --- §6 Subclass selection ---

sub_char = Character("Subclassed", "fighter")
assert sub_char.set_subclass("champion") is False  # level 1, too low
sub_char.level_up(3)
assert sub_char.set_subclass("does_not_exist") is False
assert sub_char.set_subclass("champion") is True
assert sub_char.subclass == "champion"
assert sub_char.choices["fighter_subclass"] == "champion"

print("Subclass selection test passed")

# --- §2 Serializer ---

serial_char = Character("Serial", "fighter", background_name="guard", race_name="human")
for a in ABILITIES:
    serial_char.set_ability(a, 14)
serial_char.set_hp(serial_char.max_hp)
serial_char.add_item("chain_mail")
serial_char.equip_armor("chain_mail")

payload = serial_char.to_dict()
json.dumps(payload)  # must not raise / must not need a custom encoder

assert payload["name"] == "Serial"
assert payload["class"]["id"] == "fighter"
assert payload["class"]["hit_die"] == "d10"
assert payload["race"]["id"] == "human"
assert payload["background"]["id"] == "guard"
assert payload["vitals"]["max_hp"] == serial_char.max_hp
assert payload["vitals"]["hit_dice_total"] == serial_char.hit_dice_total
assert isinstance(payload["proficiencies"]["armor"], list)
assert all(isinstance(v, str) for v in payload["proficiencies"]["armor"])

feature_by_id = {f["id"]: f for f in payload["features"]}
assert feature_by_id["second_wind"]["kind"] == "active"
assert "max_use" in feature_by_id["second_wind"]
assert feature_by_id["fighting_style"]["kind"] == "choice"
assert "chosen_value" in feature_by_id["fighting_style"]
assert feature_by_id["alert"]["kind"] == "passive"
assert feature_by_id["alert"]["source"] == "background"

print("Serializer test passed")

# --- §8 Persistence ---

with tempfile.TemporaryDirectory() as tmp_dir:
    save_path = os.path.join(tmp_dir, "character.json")
    persistence.save(serial_char, save_path)

    with open(save_path, "r", encoding="utf-8") as f:
        saved_raw = json.load(f)
    assert saved_raw["name"] == "Serial"
    assert "max_hp" not in saved_raw  # derived state is not persisted

    reloaded = persistence.load(save_path)
    assert reloaded.name == serial_char.name
    assert reloaded.current_hp == serial_char.current_hp
    assert reloaded.max_hp == serial_char.max_hp
    assert reloaded.equipped_armor is not None
    assert reloaded.equipped_armor.id == "chain_mail"
    assert {e.item.id for e in reloaded.inventory} == {e.item.id for e in serial_char.inventory}

print("Persistence roundtrip test passed")