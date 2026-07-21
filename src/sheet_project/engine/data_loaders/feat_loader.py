import json

from sheet_project.engine.features.feat import Feat
from sheet_project.engine.features.feature import Feature


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_features(raw_features: list[dict]) -> list[Feature]:
    return [
        Feature(
            type=f["type"],
            target=f.get("target"),
            operation=f.get("operation"),
            value=f.get("value"),
            conditions=f.get("conditions", []),
            metadata=f.get("metadata", {})
        )
        for f in raw_features
    ]


def load_feats(path: str) -> dict[str, Feat]:
    data = load_json(path)
    feats = {}

    for feat_id, raw_feat in data["feats"].items():

        feats[feat_id] = Feat(
            id=raw_feat["id"],
            category=raw_feat["category"],
            name=raw_feat["name"],
            description=raw_feat["description"],
            features=load_features(
                raw_feat.get("features", [])
            )
        )

    return feats
