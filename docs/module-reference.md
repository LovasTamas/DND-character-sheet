# Module reference

File-by-file breakdown of `src/sheet_project/engine/` and the tester.
Sizes/behaviors reflect the current state of the code; symbol names are
what a caller would actually import.

## `engine/paths.py`

```python
DATA_DIR = Path(__file__).resolve().parents[3] / "data"
```

Single source of truth for the location of the `data/` directory.
`parents[3]` climbs `engine/ → sheet_project/ → src/ → <repo root>`.
Every loader reads `DATA_DIR / "<file>.json"`.

## `engine/rest_type.py`

```python
class RESTTYPE(Enum):
    SHORT = "short_rest"
    LONG = "long_rest"
```

Passed to `Character.rest` and read inside `ActiveFeature.rest` via
`rest_type.value` to key into `resource.recharge`.

## `engine/character.py`

The only class the outside world instantiates. Detailed lifecycle in
[character-lifecycle.md](./character-lifecycle.md).

Public surface (what most callers touch):

- **Constructor**: `Character(name, class_name, background_name=None, race_name=None)`
- **Properties**: `proficiency_bonus`, `max_hp`, `hit_dice_total`
- **Mutation**: `set_name`, `set_ability`, `add_skill_prof`, `remove_skill_prof`,
  `set_hp`, `set_temporary_hp`, `take_damage`, `heal`, `use_feature`, `rest`,
  `spend_hit_die`, `level_up`, `set_background_ability_bonuses`,
  `set_class`, `set_race`, `set_background`, `set_subclass`,
  `add_item`, `remove_item`, `equip_weapon`, `unequip_weapon`,
  `equip_armor`, `unequip_armor`, `equip_shield`, `unequip_shield`
- **Serialization**: `to_dict()` (full UI-facing JSON, see
  [webui-architecture.md](./webui-architecture.md#character-json-shape)),
  `to_save_dict()` / classmethod `from_save_dict(data)` (input-state-only
  round trip for persistence)
- **State exposed as attributes**: `name`, `level`, `character_class`,
  `background`, `race`, `subclass`, `ability_points`, `ability_modifiers`,
  `saving_throw_values`, `skills`, `skill_profs`, `tool_profs`,
  `languages`, `speed`, `size`, `creature_type`, `features`, `choices`,
  `current_hp`, `temporary_hp`, `hit_dice_remaining`, `initiative`,
  `passive_perception`, `inventory`, `equipped_weapons`,
  `equipped_armor`, `equipped_shield`, `ac`.

Private helpers: `_merge_features`, `_recompute_skill_prof_union`,
`_initialize_features`, `_seed_inventory_from_background`,
`_prune_stale_choices`, `_feature_source`, `_skill_sources`,
`_find_in_inventory`, `_apply_single_modifier`,
`_apply_attribute_modifier`, `_apply_dict_modifier`,
`_resolve_modifier_value`.

## `engine/classes/`

### `abilities.py`

```python
class ABILITIES(Enum):  # strength, dexterity, constitution,
                        # intelligence, wisdom, charisma
```

### `proficiencies.py`

Enums: `ARMORPROF` (light/medium/heavy/shield), `WEPPROF`
(martial/simple), `SKILLPROF` (18 skills).

`SKILL_TO_ABILITY: dict[SKILLPROF, ABILITIES]` — canonical mapping used
by `Character.calculate_skills`. Any new skill in `SKILLPROF` must be
added here too, or `calculate_skills` will `KeyError`.

### `hitpoints.py`

```python
@dataclass(frozen=True)
class HitPointProgression:
    base_hp: int
    base_hp_modifier: ABILITIES
    hp_per_level: int
    hp_per_level_modifier: ABILITIES

    def calculate(self, level, modifiers) -> int:
        # base_hp + mod[base_ability]
        # + (level - 1) * (hp_per_level + mod[per_level_ability])
```

`Character.max_hp` calls this each access.

### `character_class.py`

Frozen dataclass: `class_name, name, hitpoints, armor_profs,
weapon_profs, saving_throw_profs, features, hit_die`.

⚠ **Known type-annotation bug**: `features: set[Feature|ActiveFeature|
ChoiceFeature]` — in practice `ClassLoader` populates it with a dict
(the return value of `FeatureLoader.load_features`), not a set. The
runtime works because Python doesn't enforce the annotation; the
annotation should read `dict[str, Feature|ActiveFeature|ChoiceFeature]`.
See `PLAN.md` "Out of scope".

### `class_loader.py`

`ClassLoader(class_name).load_class(level)` — see
[loaders.md](./loaders.md#classloader). Uses helper methods for HP,
weapon/armor/saving profs, and cumulative feature-list assembly.
`ClassLoader.list_classes()` (classmethod) returns `[{id, name}, …]`
for the whole catalog without hydrating any `CharacterClass`.

## `engine/features/`

### `feature.py`

- `FeatureBase(ABC)` — reads `id`, `name`, `desc`, `type` and stores
  the raw `data` dict.
- `Feature(FeatureBase)` — passive; `rest`/`use` are no-ops.

### `active_feature.py`

`ActiveFeature(FeatureBase)`:

- Extra fields: `activation`, `resource`, `effect`, plus runtime
  `max_use`/`remaining_use`.
- `max_uses(level)` picks the largest `<= level` key from
  `resource.amount`.
- `set_values(level)` re-sizes charges non-destructively.
- `use()` decrements; `rest(rest_type)` reads `resource.recharge`.

### `choice_feature.py`

`ChoiceFeature(FeatureBase)`:

- `choose(character, value)` writes to `character.choices[self.id]`.
- No validation of the value against `self.choice` (which stores the
  raw choice spec from the JSON).

### `factory.py`

- `create_feature(data)` — dispatches on `data["type"]`
  (`"active"` → `ActiveFeature`, `"choice"` → `ChoiceFeature`, else
  `Feature`).
- `FeatureLoader(needed_features).load_features()` — reads
  `data/class_features.json` and returns
  `{id: Feature}`.

### `feat_loader.py`

`FeatLoader(needed_feats).load_features()` — same as `FeatureLoader`
but reads `data/feats.json` (top key `"feats"`). Also exposes
`FeatLoader.list_feats()` (classmethod) returning `[{id, name}, …]`.

## `engine/subclasses/`

### `subclass_loader.py`

Catalog-only loader for subclass **options** (subclass content/features
are out of scope — see `PLAN_webui_backend.md`):

```python
class SubclassLoader:
    def list_for_class(self, class_id: str) -> list[dict]: ...

    @classmethod
    def unlock_level(cls, class_id: str) -> int: ...
```

`list_for_class` reads `data/subclasses.json`. `unlock_level` looks up
`SUBCLASS_UNLOCK_LEVEL` (a `{class_id: level}` dict, defaulting to `3`)
— the minimum level `Character.set_subclass` requires before accepting
a choice.

## `engine/serialization.py`

Free functions used by `Character.to_dict()`/`to_save_dict()` to keep
serialization-shape concerns (enum → `.value`, set → sorted list,
dataclass → public fields) out of the character model itself:

- `serialize_value(value)` — recursively normalizes enums, sets,
  dicts, lists, and nested dataclasses into JSON-safe values.
- `serialize_dataclass(obj)` — serializes a dataclass's public fields
  via `serialize_value`. Used for `Weapon`/`Armor`/`Item`.
- `serialize_feature(feature, choices=None)` — emits `{id, name, desc,
  kind}` plus `max_use`/`remaining_use` for `ActiveFeature` or
  `chosen_value` (looked up from `choices`) for `ChoiceFeature`.

## `engine/persistence.py`

File-backed save/load, per `PLAN_webui_backend.md` §8:

```python
def save(character: Character, path: str | Path) -> None: ...
def load(path: str | Path) -> Character: ...
```

`save` writes `character.to_save_dict()` to a temp file then
`os.replace`s it into place (atomic on POSIX). `load` reads the JSON
and rebuilds via `Character.from_save_dict`. Callers should always go
through this module rather than opening character JSON files directly.

## `engine/backgrounds/`

### `background.py`

```python
@dataclass(frozen=True)
class Background:
    id: str
    name: str
    ability_options: tuple[ABILITIES, ABILITIES, ABILITIES]
    skill_profs: set[SKILLPROF]
    tool_prof: str | None
    languages: set[str]
    feat: Feature       # already resolved
    equipment: list[str]
```

### `background_loader.py`

`BackgroundLoader(name).load_background()` — case-insensitive lookup;
raises `ValueError` on miss. Resolves `feat` id → `Feature` via
`FeatLoader`. Also exposes `BackgroundLoader.list_backgrounds()`
(classmethod) returning `[{id, name}, …]`.

## `engine/races/`

### `race.py`

```python
@dataclass(frozen=True)
class Race:
    id: str
    name: str
    size: str
    speed: int
    creature_type: str
    features: dict[str, Feature]   # already resolved via FeatureLoader
```

### `race_loader.py`

`RaceLoader(name).load_race()` — case-insensitive lookup. Race features
live in `class_features.json`, resolved via `FeatureLoader`. Silently
returns `None` if the race id is not found (contrast BackgroundLoader,
which raises). Also exposes `RaceLoader.list_races()` (classmethod)
returning `[{id, name}, …]`.

## `engine/equipment/`

Dataclasses and loaders for weapons, armor, and generic items; backs
`Character.inventory`/`equipped_*`/`ac`.

### `weapon.py`, `armor.py`, `item.py`

Frozen dataclasses matching the corresponding `data/*.json` schema (see
[data-schemas.md](./data-schemas.md)):

```python
@dataclass(frozen=True)
class Weapon:
    id: str; name: str; category: WEPPROF; type: str; damage: dict
    versatile_damage: str | None; properties: frozenset[str]
    mastery: str | None; range: dict | None; weight: int; cost: dict

@dataclass(frozen=True)
class Armor:
    id: str; name: str; category: ARMORPROF; base_ac: int; ac_bonus: int
    dex_bonus: str; strength_requirement: int | None
    stealth_disadvantage: bool; weight: int; cost: dict

@dataclass(frozen=True)
class Item:
    id: str; name: str; kind: str; weight: int; cost: dict
```

`Armor` also represents shields (`category: ARMORPROF.SHIELD`); `Item`
is the catch-all for anything that isn't a weapon or armor.

### `inventory_entry.py`

```python
@dataclass
class InventoryEntry:
    item: Weapon | Armor | Item
    quantity: int = 1
```

One entry per distinct item id in `Character.inventory`; `add_item`
increments `quantity` on the matching entry instead of duplicating it.

### `weapon_loader.py`, `armor_loader.py`, `item_loader.py`

`WeaponLoader(needed_ids).load()` / `ArmorLoader(needed_ids).load()` /
`ItemLoader(needed_ids).load()` — each reads its `data/*.json` file and
returns `{id: <dataclass>}` for exactly the requested ids. Each also
exposes a static `_build_<kind>(data)` helper that builds a single
instance from a raw JSON dict; `resolver.py` reuses these statics
directly instead of instantiating a loader per id. Each loader also
exposes a classmethod `list_weapons()` / `list_armors()` / `list_items()`
returning a lightweight `[{id, name, …}]` catalog list for UI dropdowns.

### `resolver.py`

`EquipmentResolver()` eagerly loads all three catalogs (`weapons.json`,
`armors.json`, `items.json`) once, then `.resolve(ids: list[str])`
looks up each id across the three catalogs in that order (weapon →
armor → item) and returns the matching dataclass instances. Raises
`KeyError("Unknown equipment id: <id>")` if an id isn't found in any of
them. Used by `Character._seed_inventory_from_background` and by
`Character.add_item` when given a string id.

## `tests/engine_tester.py`

Not a real test framework — just an executable script that:

1. Builds a basic Fighter, sets all abilities to 11, adds Acrobatics
   proficiency, prints `max_hp`, `proficiency_bonus`, `skills`,
   `skill_profs`.
2. Builds a **Guard/Human Fighter**, applies +2 STR / +1 WIS from
   background, sets all abilities to 10, and asserts:
   - `SKILLPROF.ATHLETICS` and `SKILLPROF.PERCEPTION` are proficient.
   - `"alert"` is in `features`.
   - `initiative == DEX modifier + proficiency_bonus` (Alert works).
   - `STR modifier == 1` (background bonus applied).
3. Builds a **Soldier/Human Fighter**, applies +2 STR / +1 CON, and
   asserts:
   - `SKILLPROF.ATHLETICS` and `SKILLPROF.INTIMIDATION` are proficient.
   - `"savage_attacker"` is in `features`.
   - `initiative == DEX modifier` (no modifier on Savage Attacker).
4. On the Guard/Human Fighter, asserts inventory/AC behavior:
   - Naked AC is `10 + DEX modifier`.
   - Background equipment (`spear`, `light_crossbow`) is auto-seeded
     into `inventory` (not equipped).
   - Adding + equipping `chain_mail` and a `shield` yields
     `16 (heavy, ignores DEX) + 2 (shield) = 18`.
   - Unequipping the shield drops AC back to `16`.
5. Builds a **Soldier** and asserts its background equipment
   (`spear`, `shortbow`, `20_arrows`) is seeded into `inventory`.

Run with:

```bash
PYTHONPATH=src python -m sheet_project.tests.engine_tester
```

## `__init__.py` files

All empty. The package layout is:

```
src/__init__.py                                (empty)
src/sheet_project/engine/__init__.py           (empty)
src/sheet_project/engine/classes/__init__.py   (empty)
src/sheet_project/engine/features/__init__.py  (empty)
src/sheet_project/engine/backgrounds/__init__.py (empty)
src/sheet_project/engine/races/__init__.py     (empty)
src/sheet_project/engine/equipment/__init__.py (empty)
src/sheet_project/engine/subclasses/__init__.py  (re-exports SubclassLoader, SUBCLASS_UNLOCK_LEVEL)
```

Note that `src/sheet_project/` itself has **no `__init__.py`**; it works
because it is a namespace package. Consumers must import as
`sheet_project.engine.<x>`, i.e. `src/` is expected to be on
`PYTHONPATH`.

## Known latent issues (kept for maintainer awareness)

Recorded here because they will bite the next contributor even though
they are documented in the plan files as "out of scope":

- `Character.calculate_passive_perception` uses `13 + skills[PERCEPTION]`.
  The D&D formula is `10 + …`; this looks like a typo.
- `class_loader.load_class` silently no-ops on unknown class ids.
- `class_loader.load_feature_list` swallows all exceptions with a bare
  `except`.
- `race_loader.load_race` returns `None` on unknown race id.
- `character_class.features` annotation says `set[...]` but is populated
  with a `dict`.
- `class_loader.load_class` contains the vestigial line
  `self.class_name = self.class_name`.
