# Architecture

The engine is a **thin composition layer** over four independent data
sources. There is no framework, no ORM, no IO abstraction — just JSON,
dataclasses, and one aggregator (`Character`).

## Component overview

```
┌──────────────────── data/ (JSON) ────────────────────┐
│  classes.json   class_features.json   feats.json     │
│  backgrounds.json                     races.json     │
└──────────────────────────────────────────────────────┘
                       │  read by
                       ▼
┌──────────────────── loaders ─────────────────────────┐
│  ClassLoader   BackgroundLoader   RaceLoader         │
│         └──────► FeatureLoader  ◄── (used by class   │
│                                     and race)        │
│               FeatLoader                             │
│               (used by BackgroundLoader)             │
└──────────────────────────────────────────────────────┘
                       │  build
                       ▼
┌────────── frozen dataclasses ────────────────────────┐
│  CharacterClass    Background    Race                │
│  HitPointProgression                                 │
│  Feature / ActiveFeature / ChoiceFeature             │
└──────────────────────────────────────────────────────┘
                       │  composed by
                       ▼
┌──────────────── Character (mutable) ─────────────────┐
│  ability_points, ability_modifiers, skills,          │
│  saving_throw_values, initiative, passive_perception │
│  speed, size, creature_type                          │
│  features (merged), choices                          │
│  skill_profs (union of per-source sets)              │
│                                                      │
│  update_automatic_values() ← recomputes derived      │
│  apply_modifiers()          ← declarative overlay    │
└──────────────────────────────────────────────────────┘
```

## Layering

1. **JSON data** — the source of truth for content. Never imported by Python
   directly; only reached via loaders.
2. **Loaders** — one loader per data file. Each loader is a small class
   with a constructor that takes a single id (e.g. `class_name`) and a
   `load_*` method that returns a frozen dataclass. Loaders are the *only*
   layer that knows the JSON schema.
3. **Dataclasses** — immutable, hashable, and behavior-light. They carry
   pre-resolved objects (e.g. `Background.feat` is a `Feature` instance,
   not a string id) so `Character` never has to touch the loaders again.
4. **`Character`** — the mutable aggregate. It owns rolled stats, the
   current level, chosen skill proficiencies, current HP, and per-feature
   state. It also owns all *derived* values (modifiers, saves, skills,
   passive perception, initiative).

## Two axes of state

`Character` distinguishes between:

- **Input state** the player controls:
  - `ability_points`, `level`, `background_ability_bonuses`,
    `skill_profs_from_player`, `current_hp`, feature charges, chosen
    `choices`.
- **Derived state** recomputed from input + content:
  - `ability_modifiers`, `saving_throw_values`, `skills`, `initiative`,
    `passive_perception`, `max_hp` (property), `proficiency_bonus`
    (property), and the union `skill_profs`.

`update_automatic_values()` is the single seam that regenerates derived
state; every mutation method calls it after changing input state.

## Data-flow sequence (typical construction)

```
Character("Tomi", "fighter", background_name="guard", race_name="human")
│
├── ClassLoader("fighter").load_class(level=1)
│       └── FeatureLoader([...]).load_features()          # class features
│
├── BackgroundLoader("guard").load_background()
│       └── FeatLoader(["alert"]).load_features()         # background feat
│
├── RaceLoader("human").load_race()
│       └── FeatureLoader([...]).load_features()          # race features
│
├── _merge_features()      # class features ∪ race features ∪ {background.feat}
├── update_automatic_values()
│       ├── _recompute_skill_prof_union()
│       ├── calculate_ability_modifiers()   # includes background ASI
│       ├── calculate_saving_throw_values()
│       ├── calculate_skills()
│       ├── calculate_passive_perception()
│       └── apply_modifiers()               # declarative overlay
└── _initialize_features()  # sets ActiveFeature.max_use / remaining_use
```

## Design conventions

- **cwd-independence.** All loaders resolve paths through
  `paths.DATA_DIR`, computed from `__file__`. Never `os.getcwd()`.
- **Enums over strings.** `ABILITIES`, `SKILLPROF`, `WEPPROF`,
  `ARMORPROF`, `RESTTYPE` are enums whose values match the JSON strings
  exactly, so loaders can call `EnumType(json_string)` directly.
- **Frozen dataclasses for content, plain classes for state.** Content
  types (`CharacterClass`, `Background`, `Race`, `HitPointProgression`)
  are `@dataclass(frozen=True)`. `Character` and the `Feature` hierarchy
  are mutable because they carry runtime state (charges, chosen values,
  current HP, etc.).
- **Per-source sets, unioned on demand.** Any collection that can come
  from multiple sources (currently only `skill_profs`) is stored as
  separate sets and unioned inside `_recompute_skill_prof_union`. This
  makes swapping a source cheap and side-effect free.
- **Modifiers are data, not code.** Passive numeric effects live in the
  JSON as `modifiers: [{target, op, value}, …]` and are applied by a
  generic dispatcher in `Character.apply_modifiers`. See
  [features-and-modifiers.md](./features-and-modifiers.md).

## Explicit non-goals (as of today)

Recorded in `PLAN_races_backgrounds.md` and still true:

- No multiclassing.
- No inventory / equipment model (`Background.equipment` is a raw id list).
- No persistence (no save/load).
- No richer modifier vocabulary (advantage/disadvantage, resistances,
  conditional triggers, spellcasting).
- No feat prerequisites, no level-4 ASI/feat choices.
- Class features and race features live in the same `class_features.json`
  pool; splitting is deferred.
