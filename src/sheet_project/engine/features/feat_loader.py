from sheet_project.engine.paths import DATA_DIR
from .factory import create_feature
import json


class FeatLoader:
    def __init__(self, needed_feats: list):
        self.path_to_features = DATA_DIR / "feats.json"
        self.needed_feats = needed_feats

    def load_features(self) -> dict:
        with open(self.path_to_features, "r", encoding="utf-8") as f:
            raw = json.load(f)['feats']
            features_to_return = {}
            for feat in self.needed_feats:
                feature_block = raw[feat]
                created_feature = create_feature(feature_block)
                features_to_return[feat] = created_feature
        return features_to_return
