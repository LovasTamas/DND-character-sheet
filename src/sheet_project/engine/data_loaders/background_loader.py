import json

from sheet_project.engine.backgrounds.background import Background, AbilityChoice
from sheet_project.engine.classes.hitpoints import HitPointProgression
from sheet_project.engine.classes.abilities import ABILITIES
from sheet_project.engine.classes.proficiencies import SKILLPROF, ARMORPROF, WEPPROF
from sheet_project.engine.classes.progression import FeatureRequirement
from sheet_project.engine.features.feat import Feat
from sheet_project.engine.data_loaders.feat_loader import load_feats


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

def handle_ability_choice(data: dict) -> AbilityChoice:
    abilities = tuple(
        ABILITIES(x)
        for x in data["options"]
    )

    return AbilityChoice(
        options=abilities,
        count=data["count"]
    )

def handle_skill_profs(profs: list[str]) -> set[SKILLPROF]:
    empty_set = set()
    for prof in profs:
        empty_set.add(SKILLPROF(prof))
    return empty_set

def handle_features(features: list[dict]) -> list[Feat]:
    feature_list = []
    for entry in features:
        if entry['type'] == "feat":
            feats = load_feats("data/feats.json")
            feature_list.append(feats[entry['id']])
    return feature_list


def load_backgroundss(path: str) -> dict[str, Background]:
    data = load_json(path)
    backgrounds = {}

    for background_id, raw_background in data["backgrounds"].items():
        backgrounds[background_id] = Background(
            background_id,
            raw_background['name'],
            ability_choice=handle_ability_choice(raw_background["ability_score_options"]
            ),
            skill_profs=handle_skill_profs(
            raw_background["proficiencies"]["skills"]
            ),
            tool_profs=set(
            raw_background["proficiencies"]["tools"]
            ),
            languages=set(
            raw_background["proficiencies"]["languages"]
            ),
            feats=handle_features(
            raw_background["features"]
            ),
            equipment=raw_background["equipment"])
    return backgrounds



classes = load_backgroundss("data/backgrounds.json")

for class_ in classes:
    print(class_)

print(classes)