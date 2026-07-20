from .active_feature import ActiveFeature
from .choice_feature import ChoiceFeature
from .feature import Feature
from sheet_project.engine.paths import DATA_DIR
import json


def create_feature(data):

    feature_type = data["type"]

    if feature_type == "active":
        return ActiveFeature(data)

    if feature_type == "choice":
        return ChoiceFeature(data)

    return Feature(data)


class FeatureLoader:
    def __init__(self, needed_features: list):
        self.path_to_features = DATA_DIR / "class_features.json"
        self.needed_features = needed_features

    def load_features(self):
        with open(self.path_to_features, "r", encoding="utf-8") as f:
            raw = json.load(f)['features']
            features_to_return = {}
            for feat in self.needed_features:
                feature_block = raw[feat]
                created_feature = create_feature(feature_block)
                features_to_return[feat] = created_feature
        return features_to_return
