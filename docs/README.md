# DND-character-sheet — Documentation

A small Python engine that models a **D&D 2024** character as
**class + background + race**, driven entirely by JSON data files
(`data/*.json`) plus a handful of loaders and dataclasses.

This documentation captures the layout, logic, and conventions of the
codebase as it exists in `src/sheet_project/`.

## Index

| Document | What it covers |
| --- | --- |
| [architecture.md](./architecture.md) | Component diagram, how data flows from JSON → loaders → `Character` |
| [data-schemas.md](./data-schemas.md) | Shape of every file in `data/` |
| [character-lifecycle.md](./character-lifecycle.md) | Construction, `update_automatic_values`, `level_up`, mutation methods |
| [features-and-modifiers.md](./features-and-modifiers.md) | `Feature` hierarchy, factory, and the declarative modifier system |
| [loaders.md](./loaders.md) | The four loaders (`ClassLoader`, `FeatureLoader`, `FeatLoader`, `BackgroundLoader`, `RaceLoader`) and their shared pattern |
| [module-reference.md](./module-reference.md) | File-by-file walkthrough of `src/sheet_project/engine/` |
| [glossary.md](./glossary.md) | D&D and engine-specific terms used throughout the code |
| [vision.md](./vision.md) | Original short vision statement for the Web UI |
| [webui-vision.md](./webui-vision.md) | Elaborated Web UI specification: layout, screens, interactions, per-region rules |
| [webui-architecture.md](./webui-architecture.md) | Web UI technical architecture: stack, project layout, API contract, deployment |

## Quick project map

```
DND-character-sheet/
├── data/                       # Pure JSON data — the game content
│   ├── classes.json            # Class definitions (Fighter, …)
│   ├── class_features.json     # Class *and* race features (shared pool)
│   ├── feats.json              # Feats (Alert, Savage Attacker, …)
│   ├── backgrounds.json        # 2024 backgrounds (Guard, Soldier, …)
│   ├── races.json              # 2024 species (Human, Elf, …)
│   ├── weapons.json            # Weapon catalog (Spear, Shortbow, …)
│   ├── armors.json             # Armor + shield catalog
│   ├── items.json              # Generic gear/ammunition catalog
│   ├── subclasses.json         # Subclass option catalog (content stays out of scope)
│   └── characters/             # Persisted character save files (engine.persistence)
│
├── src/sheet_project/
│   └── engine/
│       ├── character.py        # Central aggregator — the only class the caller uses
│       ├── paths.py            # DATA_DIR helper (cwd-independent)
│       ├── rest_type.py        # RESTTYPE enum (short / long rest)
│       ├── serialization.py    # Enum/set/dataclass/feature -> JSON-safe dict helpers
│       ├── persistence.py      # File-backed save/load (Character.to_save_dict round trip)
│       │
│       ├── classes/            # CharacterClass + supporting types (HP, profs, abilities)
│       ├── features/           # Feature hierarchy + FeatureLoader/FeatLoader/factory
│       ├── backgrounds/        # Background dataclass + BackgroundLoader
│       ├── races/              # Race dataclass + RaceLoader
│       ├── subclasses/         # SubclassLoader (catalog-only; no subclass content yet)
│       └── equipment/          # Weapon/Armor/Item dataclasses + loaders + EquipmentResolver
│
├── src/sheet_project/tests/
│   └── engine_tester.py        # Ad-hoc runnable smoke/integration test
│
├── PLAN.md                     # Historical plan: fix cwd-dependent loading (done)
├── PLAN_races_backgrounds.md   # Historical plan: races/backgrounds/feats (done)
├── PLAN_inventory_ac.md        # Historical plan: inventory + AC (done)
└── PLAN_webui_backend.md       # Active plan: backend gaps to unblock the Web UI
```

## Running the tester

The tester is a plain script; it must be importable as `sheet_project.tests.engine_tester`:

```bash
cd <repo>
PYTHONPATH=src python -m sheet_project.tests.engine_tester
```

Data-file lookup is **cwd-independent** — `paths.DATA_DIR` is derived from the
location of `paths.py`, not `os.getcwd()`, so the engine can be launched from
any directory.

## Design intent at a glance

- **Data-first.** Content lives in JSON; Python code is (mostly) generic
  machinery. Adding a class/race/background/feat is a data change, not a
  code change (unless it needs new modifier semantics).
- **One-way construction.** Loaders read JSON → build frozen dataclasses
  (`CharacterClass`, `Background`, `Race`) → `Character` composes them.
- **Layered proficiencies.** Skill proficiencies are stored per-source
  (`_from_class` / `_from_background` / `_from_player`) and unioned into
  the public `skill_profs`, so a source can be replaced without side
  effects.
- **Declarative modifiers.** Passive numeric effects (Alert → `initiative
  += proficiency_bonus`) are expressed as `{target, op, value}` JSON, not
  Python code. See [features-and-modifiers.md](./features-and-modifiers.md).
- **Single public entrypoint.** Callers only need to instantiate
  `Character(name, class_name, background_name=..., race_name=...)` and
  call its mutation methods; everything else is internal.
