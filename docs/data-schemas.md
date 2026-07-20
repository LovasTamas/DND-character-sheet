# Data schemas

Every file in `data/` is plain JSON, loaded lazily by the corresponding
loader. Enum-valued fields must use the exact `value` of the matching
Python enum — loaders call `EnumType(string)` on them.

## `data/classes.json`

Top-level shape: `{ "classes": [ … ] }`.

Each class entry:

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Matched case-insensitively against the constructor argument (`Character(..., class_name=…)`). |
| `name` | string | Display name. |
| `saving_prof` | `list[string]` | Values from `ABILITIES` (`strength`, `dexterity`, …). |
| `wep_prof` | `list[string]` | Values from `WEPPROF` (`simple`, `martial`). |
| `armor_prof` | `list[string]` | Values from `ARMORPROF` (`light`, `medium`, `heavy`, `shield`). |
| `features` | `{ "<level>": [feature_id, …] }` | Level → list of ids into `class_features.json`. Loaded cumulatively up to the character's current level. |
| `hp.first_level` | `"<int>\|<ability>"` | E.g. `"10\|constitution"`. Parsed by `ClassLoader.handle_hp`. |
| `hp.per_level` | `"<int>\|<ability>"` | E.g. `"6\|constitution"`. |
| `hit_die` | string | E.g. `"d10"`. Stored verbatim on `CharacterClass.hit_die`; surfaced to the UI via `Character.spend_hit_die()` and the `vitals.hit_die` field of `to_dict()`. |
| `size` | string | Currently unread by the engine (race supplies size). |
| `speed` | int | Currently unread by the engine (race supplies speed). |

Example (fighter):

```json
{
  "id": "fighter",
  "saving_prof": ["strength", "constitution"],
  "wep_prof": ["simple", "martial"],
  "armor_prof": ["light", "medium", "heavy", "shield"],
  "features": {
    "1": ["fighting_style", "second_wind", "weapon_mastery"],
    "2": ["action_surge", "tactical_mind"],
    "3": ["fighter_subclass"]
  },
  "hp": { "first_level": "10|constitution", "per_level": "6|constitution" },
  "hit_die": "d10"
}
```

## `data/class_features.json`

Top-level shape: `{ "features": { "<id>": { … } } }`.

Despite the filename, this file also stores **race features**
(`darkvision_60`, `keen_senses`, `resourceful`, …) — the split is
historical and both `FeatureLoader` and `RaceLoader` read from the same
file. It also holds the `fighter_subclass` `ChoiceFeature` stub
referenced by `classes.json` at level 3 — see `data/subclasses.json`
below for the actual catalog of subclass options.

Every feature entry has:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | string | ✓ | Must equal the object key. |
| `name` | string | ✓ | Display name. |
| `desc` | string | ✓ | Human-readable description. |
| `type` | `"passive" \| "active" \| "choice"` | ✓ | Selects the Python subclass (see [features-and-modifiers.md](./features-and-modifiers.md)). |
| `modifiers` | `list[Modifier]` | optional | Declarative numeric effects. Only read by `Character.apply_modifiers`. |

Type-specific extras:

- **`type: "active"`** — used by `ActiveFeature`:
  - `activation`: e.g. `"bonus_action"` (stored but not interpreted).
  - `resource.type`: e.g. `"charges"`.
  - `resource.amount`: `{ "<level>": <int> }` — the largest level ≤ the
    character's current level wins (see `ActiveFeature.max_uses`).
  - `resource.recharge`: `{ "short_rest": <int>, "long_rest": <int> }` —
    `-1` means "recharge to full", positive integers are additive up to
    max, `0`/absent means the rest doesn't recharge this feature.

- **`type: "choice"`** — used by `ChoiceFeature`:
  - `choice.source`: string tag (e.g. `"fighting_styles"`), currently
    not validated against any catalog.
  - `choice.amount`: either an int or `{ "<level>": <int> }` — stored
    verbatim; scaling logic is not implemented yet.

## `data/feats.json`

Top-level shape: `{ "feats": { "<id>": { … } } }`.

Same schema as an entry in `class_features.json`. Loaded by
`FeatLoader`; used exclusively by `BackgroundLoader` today. Two feats
ship with the engine:

- `alert` — `modifiers: [{ "target": "initiative", "op": "add", "value": "proficiency_bonus" }]`
- `savage_attacker` — `modifiers: []` (descriptive only; the current
  modifier vocabulary can't express damage-roll rerolls).

## `data/backgrounds.json`

Top-level shape: `{ "backgrounds": [ … ] }`.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Matched case-insensitively. |
| `name` | string | Display name. |
| `ability_options` | `list[string]` (length 3) | Values from `ABILITIES`. The three abilities the player may distribute +2/+1 or +1/+1/+1 across. |
| `skill_profs` | `list[string]` | Values from `SKILLPROF`. |
| `tool_prof` | string \| null | Free-form (no enum). Stored in `Character.tool_profs`. |
| `languages` | `list[string]` | Free-form. Stored in `Character.languages`. |
| `feat` | string | Id into `feats.json`. Resolved to a `Feature` instance on load. |
| `equipment` | `list[string]` | Ids into `weapons.json` / `armors.json` / `items.json`. Resolved by `EquipmentResolver` and seeded into `Character.inventory` on construction (see [character-lifecycle.md](./character-lifecycle.md)). |

## `data/races.json`

Top-level shape: `{ "races": [ … ] }`.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Matched case-insensitively. |
| `name` | string | Display name. |
| `size` | string | Free-form (`"medium"`, …). Currently just stored on `Character.size`. |
| `speed` | int | Base walking speed in feet; assigned to `Character.speed`. |
| `creature_type` | string | E.g. `"humanoid"`. Stored on `Character.creature_type`. |
| `features` | `list[string]` | Ids into `class_features.json` (yes, the same file class features live in). |

## `data/weapons.json`

Top-level shape: `{ "weapons": { "<id>": { … } } }`.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Must equal the object key. |
| `name` | string | Display name. |
| `category` | string | Value from `WEPPROF` (`simple`, `martial`). |
| `type` | string | `"melee"` or `"ranged"`. Free-form (no enum). |
| `damage` | `{ dice, ability, damage_type }` | `ability` is a free-form ability name string, not validated against `ABILITIES`. |
| `versatile_damage` | string \| null | Extra dice when wielded two-handed. |
| `properties` | `list[string]` | Free-form (`thrown`, `versatile`, `ammunition`, …). Loaded into a `frozenset`. |
| `mastery` | string \| null | Free-form weapon mastery keyword. |
| `range` | `{ normal, long }` \| null | Feet. |
| `weight` | int | |
| `cost` | `{ amount, unit }` | |

Loaded by `WeaponLoader`; resolved via `EquipmentResolver` into the
`Weapon` dataclass (`src/sheet_project/engine/equipment/weapon.py`).

## `data/armors.json`

Top-level shape: `{ "armors": { "<id>": { … } } }`.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Must equal the object key. |
| `name` | string | Display name. |
| `category` | string | Value from `ARMORPROF` (`light`, `medium`, `heavy`, `shield`). |
| `base_ac` | int | Base AC granted while worn (0 for shields). |
| `ac_bonus` | int | Flat AC bonus added on top of `base_ac` (used by shields). |
| `dex_bonus` | string | `"full"`, `"max_2"`, or `"none"` — how much of the DEX modifier applies. Interpreted by `Character.calculate_ac`. |
| `strength_requirement` | int \| null | Currently unread by the engine. |
| `stealth_disadvantage` | bool | Currently unread by the engine. |
| `weight` | int | |
| `cost` | `{ amount, unit }` | |

Loaded by `ArmorLoader`; resolved via `EquipmentResolver` into the
`Armor` dataclass (`src/sheet_project/engine/equipment/armor.py`). Also
used for shields (`category: "shield"`), which `equip_shield` requires.

## `data/items.json`

Top-level shape: `{ "items": { "<id>": { … } } }`.

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Must equal the object key. |
| `name` | string | Display name. |
| `kind` | string | Free-form (`"gear"`, `"ammunition"`, …); no enum. |
| `weight` | int | |
| `cost` | `{ amount, unit }` | |

Loaded by `ItemLoader`; resolved via `EquipmentResolver` into the `Item`
dataclass (`src/sheet_project/engine/equipment/item.py`). Catch-all for
equipment that is neither a weapon nor armor.

## `data/subclasses.json`

Top-level shape: `{ "subclasses": { "<class_id>": [ { "id", "name" }, … ] } }`.

A catalog-only file: it enumerates subclass *options* for a dropdown.
Subclass **features** are out of scope (see
[`../PLAN_webui_backend.md`](../PLAN_webui_backend.md#out-of-scope-intentionally-deferred)).
Loaded by `SubclassLoader.list_for_class(class_id)`
(`src/sheet_project/engine/subclasses/subclass_loader.py`), which also
exposes `SubclassLoader.unlock_level(class_id)` — the minimum
character level required before `Character.set_subclass` accepts a
choice (currently `3` for every modeled class).

## Catalog listing helpers

Every loader above additionally exposes a `list_*` classmethod (e.g.
`ClassLoader.list_classes()`, `BackgroundLoader.list_backgrounds()`,
`RaceLoader.list_races()`, `FeatLoader.list_feats()`,
`WeaponLoader.list_weapons()`, `ArmorLoader.list_armors()`,
`ItemLoader.list_items()`) that returns a lightweight `[{id, name, …}]`
list without hydrating full dataclass instances — intended for UI
dropdowns.

## Modifier objects (used inside `modifiers: [...]`)

Same shape everywhere; documented in
[features-and-modifiers.md](./features-and-modifiers.md#the-modifier-object).

```json
{ "target": "initiative", "op": "add", "value": "proficiency_bonus" }
```

## Data conventions

- **All string enum values are lowercased** and use `snake_case`. Enum
  classes mirror this in their `.value`.
- **All ids are lowercased snake_case** and used as dict keys /
  cross-references.
- **File encoding is UTF-8**; loaders open with `encoding="utf-8"`.
- **Feature ids are globally unique** across `class_features.json` and
  `feats.json` in practice. If a race feature and a class feature ever
  collide, `_merge_features` (dict-union) would silently pick one — see
  the merge order in [character-lifecycle.md](./character-lifecycle.md#feature-merging).
