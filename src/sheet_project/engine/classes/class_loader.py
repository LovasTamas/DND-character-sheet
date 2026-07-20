import json
from sheet_project.engine.classes.abilities import ABILITIES
from sheet_project.engine.classes.proficiencies import SKILLPROF, WEPPROF, ARMORPROF
from sheet_project.engine.classes.hitpoints import HitPointProgression
from sheet_project.engine.classes.character_class import CharacterClass
from sheet_project.engine.features.factory import FeatureLoader
from sheet_project.engine.paths import DATA_DIR


class ClassLoader:
    def __init__(self, class_name: str):
        self.path_to_data = DATA_DIR / "classes.json"
        class_name = class_name.lower()
        self.class_name = class_name
    
    def handle_hp(self, class_json):
        base_hp_string = class_json['hp']['first_level'].split('|')
        base_hp_value = int(base_hp_string[0])
        base_hp_modifier = ABILITIES(base_hp_string[-1])
        hp_per_level_string = class_json['hp']['per_level'].split('|')
        hp_per_level_value = int(hp_per_level_string[0])
        hp_per_level_modifier = ABILITIES(hp_per_level_string[-1])
        character_hp_progression = HitPointProgression(base_hp=base_hp_value, base_hp_modifier=base_hp_modifier, hp_per_level=hp_per_level_value, hp_per_level_modifier=hp_per_level_modifier)
        return character_hp_progression
    
    def load_wep_profs(self, class_json):
        wep_profs = class_json['wep_prof']
        empty_set = set()
        for prof in wep_profs:
            empty_set.add(WEPPROF(prof))
        return empty_set

    def load_armor_profs(self, class_json):
        armor_profs = class_json['armor_prof']
        empty_set = set()
        for prof in armor_profs:
            empty_set.add(ARMORPROF(prof))
        return empty_set

    def load_saving_profs(self, class_json):
        saving_profs = class_json['saving_prof']
        empty_set = set()
        for prof in saving_profs:
            empty_set.add(ABILITIES(prof))
        return empty_set
    
    def load_feature_list(self, class_json, lvl: int):
        feature_list = []
        for i in range(1, lvl+1):
            try:
                level_features = class_json['features'][str(i)]
                feature_list.extend(level_features)
            except Exception as e:
                print(f"Got exception: {e}")
        return feature_list
    
    def load_class(self, level: int):
        with open(self.path_to_data, "r", encoding="utf-8") as f:
            classes = json.load(f)['classes']
            for char_class in classes:
                if char_class['id'] == self.class_name:
                    self.class_name = self.class_name
                    self.character_hp_progression = self.handle_hp(char_class)
                    self.wep_pros = self.load_wep_profs(char_class)
                    self.armor_profs = self.load_armor_profs(char_class)
                    self.saving_profs = self.load_saving_profs(char_class)
                    self.loaded_features = FeatureLoader(self.load_feature_list(char_class, level)).load_features()
        return CharacterClass(self.class_name, self.character_hp_progression, self.armor_profs, self.wep_pros, self.saving_profs, self.loaded_features)