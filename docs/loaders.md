# Loaders

All JSON I/O is confined to five loader classes. They share a common
shape and are the *only* code that knows the shape of the files in
`data/`.

## Shared pattern

```python
class SomeLoader:
    def __init__(self, id_string: str):
        self.path_to_data = DATA_DIR / "<file>.json"
        self.<id_field> = id_string.lower()

    def load_<thing>(self):
        with open(self.path_to_data, "r", encoding="utf-8") as f:
            <parse JSON, iterate entries, match by id>
            return <frozen dataclass>
```

Conventions every loader follows:

- **`DATA_DIR` from `paths.py`** — never `os.getcwd()`. This makes the
  engine importable from any working directory.
- **Case-insensitive id match** — the incoming id is lowercased in
  `__init__`; JSON ids are already lowercase.
- **UTF-8 encoding**, explicit `encoding="utf-8"`.
- **One file opened per `load_*` call** — no caching, no shared state
  across loaders. Fine for the current size; a caching layer would be
  additive.
- **Enums resolved on the way in** — `ABILITIES(...)`, `SKILLPROF(...)`,
  `ARMORPROF(...)`, `WEPPROF(...)`. Raises `ValueError` on unknown
  strings, which is the correct fail-fast behavior.

## `ClassLoader`

File: `src/sheet_project/engine/classes/class_loader.py`
Reads: `data/classes.json`
Returns: `CharacterClass`

Constructor takes `class_name`; `load_class(level)` scans the class
array for a matching `id`, then:

- **HP progression** — parses `"first_level"` and `"per_level"` strings
  of the form `"<int>|<ability>"` into a `HitPointProgression` dataclass
  via `handle_hp`.
- **Weapon/armor/saving proficiencies** — `WEPPROF(str)` /
  `ARMORPROF(str)` / `ABILITIES(str)` per element, into sets.
- **Features** — cumulative up to `level`: iterates levels `1..level`,
  reading `features[str(i)]` for each. The result is a flat list of
  feature ids that is handed to a `FeatureLoader`.

Notable quirks (documented, not fixed here):

- **`load_feature_list` swallows all exceptions with a bare `try/except`**
  and prints them. Missing level keys therefore just print a message and
  continue — you'll silently get fewer features than you expected.
- `load_class` does **nothing** if no class matches the id (returns a
  broken `CharacterClass` referring to unset instance attributes on the
  loader). Add a match guard when this becomes user-facing.
- The line `self.class_name = self.class_name` in `load_class` is a
  vestigial no-op.
- `class_features.json` also holds race features; `FeatureLoader`
  doesn't care where the id semantically comes from.

## `FeatureLoader`

File: `src/sheet_project/engine/features/factory.py`
Reads: `data/class_features.json`
Returns: `dict[str, Feature | ActiveFeature | ChoiceFeature]`

Constructor takes a list of feature ids to load. `load_features()` opens
the file once and dispatches each block through `create_feature`
(subclass selection by `type` field). Used by both `ClassLoader` and
`RaceLoader`.

Failure modes: `KeyError` if any requested id is absent from the JSON.

## `FeatLoader`

File: `src/sheet_project/engine/features/feat_loader.py`
Reads: `data/feats.json`
Returns: same dict shape as `FeatureLoader`.

Structurally a copy of `FeatureLoader` reading a different file with a
different top-level key (`"feats"` vs `"features"`). Used exclusively
by `BackgroundLoader` today to resolve `background.feat` from an id
into a `Feature` instance.

Note: since feat entries have the same schema as class-feature entries,
`create_feature` is the same factory here — a feat can in principle be
`active` or `choice`, not just `passive`.

## `BackgroundLoader`

File: `src/sheet_project/engine/backgrounds/background_loader.py`
Reads: `data/backgrounds.json`
Returns: `Background`

For each background entry, `load_background`:

- Turns `ability_options` into `tuple[ABILITIES, …]` (order-preserving).
- Turns `skill_profs` into `set[SKILLPROF]`.
- Copies `languages` into a set of raw strings (no enum).
- Resolves `feat` (an id) to a `Feature` via `FeatLoader([feat_id])`.
- Uses `background.get("tool_prof") or None` — an empty string collapses
  to `None`.
- Stores `equipment` as a raw list; no interpretation.
- Passes everything positionally to `Background(...)`. The order of
  positional args matches the field order in `background.py`.

Fails loud: raises `ValueError(f"Background '<name>' not found")` after
iterating the whole file without a match.

## `RaceLoader`

File: `src/sheet_project/engine/races/race_loader.py`
Reads: `data/races.json`
Returns: `Race`

For each race entry, `load_race`:

- Resolves `features` (list of ids) via `FeatureLoader(...)`
  — same file (`class_features.json`) that class features come from.
- Builds `Race(id, name, size, speed, creature_type, features=...)` via
  kwargs.

Fails **silently** on unknown race id (returns `None` implicitly, which
will crash the caller downstream). Contrast `BackgroundLoader`, which
raises. Worth aligning if you touch this.

## Dependency graph

```
Character
  ├── ClassLoader ──► FeatureLoader ──► class_features.json
  ├── BackgroundLoader ──► FeatLoader ──► feats.json
  └── RaceLoader ──► FeatureLoader ──► class_features.json
```

`FeatureLoader` and `FeatLoader` both go through `create_feature` in
`features/factory.py`, so adding a new feature `type` value is a
one-place change.

## When to add another loader

Only when introducing a new **data file** with its own top-level key.
Extending an existing file (adding fields or new entries) requires no
new loader — extend the parsing inside the relevant `load_*` method.
