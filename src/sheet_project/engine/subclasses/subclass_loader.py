import json

from sheet_project.engine.paths import DATA_DIR

# 2024 rules: every class currently modeled unlocks its subclass at
# level 3. Kept as a lookup (rather than a bare constant) so a future
# class with a different unlock level is a one-line addition.
SUBCLASS_UNLOCK_LEVEL: dict[str, int] = {
    "fighter": 3,
}

DEFAULT_SUBCLASS_UNLOCK_LEVEL = 3


class SubclassLoader:
    """Catalog-only loader: enumerates subclass options for a class.

    Subclass *features* are intentionally out of scope (see
    PLAN_webui_backend.md, "Out of scope"); this loader only ever
    returns `{id, name}` pairs for a dropdown.
    """

    def __init__(self):
        self.path_to_data = DATA_DIR / "subclasses.json"

    def list_for_class(self, class_id: str) -> list[dict]:
        with open(self.path_to_data, "r", encoding="utf-8") as f:
            subclasses = json.load(f)["subclasses"]
        return list(subclasses.get(class_id.lower(), []))

    @classmethod
    def unlock_level(cls, class_id: str) -> int:
        return SUBCLASS_UNLOCK_LEVEL.get(class_id.lower(), DEFAULT_SUBCLASS_UNLOCK_LEVEL)
