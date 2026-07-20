import json

from sheet_project.engine.backgrounds.background import Background
from sheet_project.engine.classes.abilities import ABILITIES
from sheet_project.engine.classes.proficiencies import SKILLPROF
from sheet_project.engine.features.feat_loader import FeatLoader
from sheet_project.engine.paths import DATA_DIR


class BackgroundLoader:
    def __init__(self, background_name: str):
        self.path_to_data = DATA_DIR / "backgrounds.json"
        background_name = background_name.lower()
        self.background_name = background_name

    def load_background(self) -> Background:
        with open(self.path_to_data, "r", encoding="utf-8") as f:
            backgrounds = json.load(f)["backgrounds"]
            for background in backgrounds:
                if background["id"].lower() == self.background_name:
                    ability_options = tuple(
                        ABILITIES(ability) for ability in background["ability_options"]
                    )
                    skill_profs = set()
                    for skill_prof in background["skill_profs"]:
                        skill_profs.add(SKILLPROF(skill_prof))
                    languages = set()
                    for language in background["languages"]:
                        languages.add(language)
                    feat_id = background["feat"]
                    feat = FeatLoader([feat_id]).load_features()[feat_id]
                    tool_prof = background.get("tool_prof") or None
                    return Background(
                        background["id"],
                        background["name"],
                        ability_options,
                        skill_profs,
                        tool_prof,
                        languages,
                        feat,
                        background["equipment"],
                    )

        raise ValueError(f"Background '{self.background_name}' not found")
