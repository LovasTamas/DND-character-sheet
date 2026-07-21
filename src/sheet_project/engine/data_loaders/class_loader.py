import json

from sheet_project.engine.classes.character_class import CharacterClass
from sheet_project.engine.classes.hitpoints import HitPointProgression
from sheet_project.engine.classes.abilities import ABILITIES
from sheet_project.engine.classes.proficiencies import SKILLPROF, ARMORPROF, WEPPROF
from sheet_project.engine.classes.progression import FeatureRequirement


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

def handle_armor_profs(profs: list[str]) -> set[ARMORPROF]:
    armor_profs = set()
    for prof in profs:
        armor_profs.add(ARMORPROF(prof))
    return armor_profs

def handle_weapon_profs(profs: list[str]) -> set[WEPPROF]:
    wep_profs = set()
    for prof in profs:
        wep_profs.add(WEPPROF(prof))
    return wep_profs

def handle_saving_profs(profs: list[str]):
        empty_set = set()
        for prof in profs:
            empty_set.add(ABILITIES(prof))
        return empty_set

def handle_features(features: list[dict]) -> list[FeatureRequirement]:
    result = []

    for feature in features:
        result.append(
            FeatureRequirement(
                level=feature["level"],
                feature_id=feature["id"],
                feature_type=feature.get("type"),
                choices=feature.get("choices")
            )
        )

    return result



def load_classes(path: str) -> dict[str, CharacterClass]:
    data = load_json(path)
    classes = {}

    for class_id, raw_class in data["classes"].items():
        base_hp = raw_class['hit_points']['first_level']
        per_level_hp = raw_class['hit_points']['per_level']
        classes[class_id] = CharacterClass(
            raw_class['name'],
            class_id,
            HitPointProgression(base_hp['base'], base_hp['ability'],
                                per_level_hp['base'], per_level_hp['ability']),
            handle_armor_profs(raw_class['proficiencies']['armor']),
            handle_weapon_profs(raw_class['proficiencies']['weapons']),
            handle_saving_profs(raw_class['saving_throws']),
            handle_features(raw_class['features']),
            raw_class['hit_points']['hit_die']
        )
    return classes



classes = load_classes("data/classes.json")

for class_ in classes:
    print(class_)

print(classes)