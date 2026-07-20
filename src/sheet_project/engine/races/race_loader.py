import json

from sheet_project.engine.features.factory import FeatureLoader
from sheet_project.engine.paths import DATA_DIR
from sheet_project.engine.races.race import Race


class RaceLoader:
    def __init__(self, race_name: str):
        self.path_to_data = DATA_DIR / "races.json"
        race_name = race_name.lower()
        self.race_name = race_name

    def load_race(self) -> Race:
        with open(self.path_to_data, "r", encoding="utf-8") as f:
            races = json.load(f)["races"]
            for race in races:
                if race["id"].lower() == self.race_name:
                    loaded_features = FeatureLoader(race["features"]).load_features()
                    return Race(
                        id=race["id"],
                        name=race["name"],
                        size=race["size"],
                        speed=race["speed"],
                        creature_type=race["creature_type"],
                        features=loaded_features,
                    )
