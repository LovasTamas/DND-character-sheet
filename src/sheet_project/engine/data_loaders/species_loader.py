import json

from sheet_project.engine.races.species import Species
from sheet_project.engine.backgrounds.background import AbilityChoice
from sheet_project.engine.classes.abilities import ABILITIES
from sheet_project.engine.features.feature import Feature


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def handle_ability_choice(data: dict | None) -> AbilityChoice | None:
    if data is None:
        return None

    abilities = tuple(
        ABILITIES(ability)
        for ability in data["options"]
    )

    return AbilityChoice(
        options=abilities,
        count=data["count"]
    )


def handle_features(
        features: list[dict],
        species_traits: dict[str, Feature]
) -> list[Feature]:

    feature_list = []

    for entry in features:
        if entry["type"] == "trait":
            feature_list.append(
                species_traits[entry["id"]]
            )

    return feature_list


def load_species(
        path: str,
        species_traits: dict[str, Feature]
) -> dict[str, Species]:

    data = load_json(path)

    species = {}

    for species_id, raw_species in data["species"].items():

        species[species_id] = Species(
            id=raw_species["id"],

            name=raw_species["name"],

            size=raw_species["size"],

            speed=raw_species["speed"],

            ability_choice=handle_ability_choice(
                raw_species.get(
                    "ability_score_options"
                )
            ),

            features=handle_features(
                raw_species["features"],
                species_traits
            )
        )

    return species
