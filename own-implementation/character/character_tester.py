import json
from character import Character
from race import Race

with open(r"D:\DND\DND-character-sheet\own-implementation\my_data\races.json", "r", encoding="utf-8") as f:
    races = json.load(f)['race']
for race in races:
    if race['name'].lower() == 'dwarf':
        selected = race
race_obj = Race(selected)
test_char = Character()
test_char.add_race(race_obj)
test_char.set_name("Tomi_test")
print(test_char)
print(test_char.race)