# Glossary

Short reference for the D&D terms used across the code and docs, plus a
few engine-specific ones. All string values shown match the enum
`.value` / JSON id used in the codebase.

## Character composition

- **Class** — the character's profession/archetype (e.g. Fighter).
  Determines HP progression, weapon/armor/saving proficiencies, and
  the leveled feature list. Data in `data/classes.json`.
- **Background** — the character's pre-adventuring history (e.g. Guard,
  Soldier). Grants skill proficiencies, a tool proficiency, languages,
  a feat, ability-score improvements, and starting equipment. Data in
  `data/backgrounds.json`.
- **Race / Species** — the character's biological kind (e.g. Human,
  Elf). Grants size, speed, creature type, and a bundle of features.
  Data in `data/races.json`. (D&D 2024 renamed "race" to "species";
  the code uses "race" throughout.)

## Ability scores

The six ability scores, from `ABILITIES` (values match `.value`):

| Name | Value |
| --- | --- |
| Strength | `"strength"` |
| Dexterity | `"dexterity"` |
| Constitution | `"constitution"` |
| Intelligence | `"intelligence"` |
| Wisdom | `"wisdom"` |
| Charisma | `"charisma"` |

- **Ability score / ability point** — the raw 1–20 value.
  `Character.ability_points`.
- **Ability modifier** — `(score - 10) // 2`, computed by
  `calculate_ability_modifiers`. Added to rolls tied to that ability.
- **Ability score improvement (ASI)** — a bonus to one or more
  ability scores. In this engine, only the background-granted ASI is
  modeled, layered on top of `ability_points` via
  `background_ability_bonuses`.

## Proficiency

- **Proficiency bonus** — `2 + (level - 1) // 4`. Applies to attacks,
  saves, and skills you're proficient in. Exposed as
  `Character.proficiency_bonus`.
- **Skill proficiency** — proficiency in one of 18 skills (`SKILLPROF`).
  Adds `proficiency_bonus` to the associated ability check.
- **Saving-throw proficiency** — proficiency in one of the six ability
  saves. Adds `proficiency_bonus` to that save.
- **Weapon proficiency** — either `"simple"` or `"martial"`
  (`WEPPROF`).
- **Armor proficiency** — `"light" / "medium" / "heavy" / "shield"`
  (`ARMORPROF`).

## Skills

The 18 skills from `SKILLPROF`, grouped by governing ability (per
`SKILL_TO_ABILITY`):

- **Strength**: Athletics
- **Dexterity**: Acrobatics, Sleight of Hand, Stealth
- **Intelligence**: Arcana, History, Investigation, Nature, Religion
- **Wisdom**: Animal Handling, Insight, Medicine, Perception, Survival
- **Charisma**: Deception, Intimidation, Performance, Persuasion

## Combat / derived stats

- **Hit Points (HP)** — health. `Character.max_hp` via
  `HitPointProgression.calculate`; `Character.current_hp` for tracking.
- **Initiative** — reaction speed in combat; base `DEX modifier`, may be
  boosted by features (Alert). Set in `calculate_ability_modifiers`,
  then adjusted by `apply_modifiers`.
- **Passive Perception** — a Perception score used implicitly.
  Formula in the engine: `13 + skills[PERCEPTION]` (note:
  D&D formula is `10 + …`; see caveat in
  [module-reference.md](./module-reference.md#known-latent-issues-kept-for-maintainer-awareness)).
- **AC (Armor Class)** — accepted as a `target` by the modifier system
  but not initialized on `Character` yet.

## Rests

`RESTTYPE`:

- **Short rest** (`"short_rest"`) — recharges some feature charges.
- **Long rest** (`"long_rest"`) — typically full recharge.

`ActiveFeature.rest(rest_type)` looks up `resource.recharge[rest_type.value]`.

## Feature terminology

- **Feature** — any trait a character has. In the JSON, everything with
  a `type` field is a feature: class features, race features, and
  feats.
  - `type: "passive"` — no charges/choices; typically only interesting
    for its `modifiers`.
  - `type: "active"` — has charges (`resource.amount`) and a recharge
    rule (`resource.recharge`).
  - `type: "choice"` — the player picks something. Choice is stored on
    `Character.choices[feature_id]`.
- **Feat** — a specific kind of feature granted (in this engine) by a
  background. Structurally identical to a class feature; stored in a
  separate JSON file (`feats.json`) for organizational clarity.
- **Modifier** — a `{target, op, value}` object attached to a feature's
  JSON that declaratively bumps a numeric character stat. See
  [features-and-modifiers.md](./features-and-modifiers.md#the-modifier-system).

## Engine-specific

- **Loader** — a class (`ClassLoader`, `BackgroundLoader`, …) whose
  only job is to read a JSON file and return a frozen dataclass. See
  [loaders.md](./loaders.md).
- **`DATA_DIR`** — path to `data/`, resolved from `paths.py`.
  Cwd-independent.
- **Per-source skill sets** — `skill_profs_from_class`,
  `skill_profs_from_background`, `skill_profs_from_player`. Unioned into
  the public `skill_profs` by `_recompute_skill_prof_union`.
- **`update_automatic_values`** — the recompute pipeline that runs after
  every input-state mutation. See
  [character-lifecycle.md](./character-lifecycle.md#update_automatic_values--the-recompute-pipeline).
