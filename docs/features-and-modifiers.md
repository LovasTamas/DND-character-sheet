# Features and modifiers

All "traits" in the engine — class features, race traits, and feats — go
through a single hierarchy rooted at `FeatureBase`. Numeric passive
effects are expressed with a small declarative **modifier** vocabulary
that `Character.apply_modifiers` interprets.

## The `Feature` hierarchy

```
FeatureBase (ABC)         src/sheet_project/engine/features/feature.py
├── Feature               plain passive; rest/use are no-ops
├── ActiveFeature         active_feature.py — has charges, activation, recharge
└── ChoiceFeature         choice_feature.py — records the player's pick on the character
```

Every subclass stores the raw JSON block on `self.data`, so downstream
consumers (like `Character.apply_modifiers`) can read arbitrary optional
fields (e.g. `data["modifiers"]`) without threading them through the
constructor.

### Shared fields (`FeatureBase.__init__`)

| Attribute | JSON key |
| --- | --- |
| `self.id` | `"id"` |
| `self.name` | `"name"` |
| `self.description` | `"desc"` |
| `self.type` | `"type"` |
| `self.data` | full raw dict |

Abstract methods `rest(rest_type)` and `use()` must be provided by
subclasses.

### `Feature` (passive)

- `rest` and `use` are no-ops.
- Passive numeric effects come from `data["modifiers"]` — not from any
  method on the feature itself. This is important: adding a passive
  effect is a **data-only** change (edit the JSON), no new subclass.

### `ActiveFeature`

Represents features with limited charges (Second Wind, Action Surge, …).

Extra fields:

- `self.activation` — free-form (`"bonus_action"`, `"reaction"`, …);
  stored but never inspected by the engine.
- `self.resource` — dict with `type`, `amount`, `recharge`.
- `self.effect` — free-form; stored but not inspected.
- `self.max_use`, `self.remaining_use` — runtime state (start at 0
  until `set_values(level)` is called by `Character._initialize_features`).

Behavior:

- **`max_uses(level)`** picks the amount for the largest level threshold
  `≤ level`. E.g. Second Wind's `{ "1": 2, "4": 3, "10": 4 }` gives 2
  charges at levels 1–3, 3 at 4–9, 4 at 10+.
- **`set_values(level)`** re-sizes on level-up while preserving already
  used charges:
  - If `max_use == 0` (first init) → `remaining_use = new_max`.
  - Otherwise `remaining_use = min(new_max, remaining_use + gained)`,
    where `gained = new_max - max_use`. So consuming a charge and then
    leveling up doesn't secretly refill.
- **`use()`** — decrements `remaining_use` if > 0 and returns `True`;
  otherwise returns `False`.
- **`rest(rest_type)`** reads `resource.recharge[rest_type.value]`:
  - `-1` → full refill.
  - positive int → add up to `max_use`.
  - missing / 0 → no effect.

### `ChoiceFeature`

Features where the player picks something (fighting style, weapon
mastery choices).

- Stores `self.choice = data["choice"]` (the raw options block).
- `choose(character, value)` writes `character.choices[self.id] = value`
  — the character-side registry. There is currently **no validation**
  that `value` is legal for the choice; that's expected to be layered
  on top later.
- `use` and `rest` are no-ops.

## The factory: `create_feature(data)`

`src/sheet_project/engine/features/factory.py`

```python
def create_feature(data):
    if data["type"] == "active":  return ActiveFeature(data)
    if data["type"] == "choice":  return ChoiceFeature(data)
    return Feature(data)
```

Every feature/feat in the codebase is instantiated through this
function — both `FeatureLoader` and `FeatLoader` call it. Adding a new
`type` string means adding a branch here and a new subclass; no other
call site changes.

## The modifier system

The **only** way today for a feature to numerically alter a character's
derived stats is via a JSON `modifiers` list on the feature. This is
what makes `Alert → initiative += proficiency_bonus` a pure data change.

### The modifier object

```json
{ "target": "<string>", "op": "add" | "set", "value": <int | string> }
```

- `target` (string) — where to apply. See vocabulary below.
- `op` (string) — how to apply. Only `"add"` and `"set"` are recognized.
  Any other value is silently ignored.
- `value` — either a literal `int` or a symbolic string (see below).

### Supported `target` vocabulary

Implemented in `Character._apply_single_modifier`:

**Direct attribute targets** (mutate `Character` scalar attributes):

| Target | Attribute mutated |
| --- | --- |
| `initiative` | `self.initiative` |
| `passive_perception` | `self.passive_perception` |
| `ac` | `self.ac` — initialized to `10` in `__init__`, recomputed each pipeline run by `calculate_ac` from `equipped_armor`/`equipped_shield` before modifiers apply. |

**Prefixed dict targets** (mutate keys inside a dict):

| Prefix | Dict | Key enum | Example |
| --- | --- | --- | --- |
| `ability.` | `self.ability_modifiers` | `ABILITIES` | `ability.strength` |
| `skill.` | `self.skills` | `SKILLPROF` | `skill.perception` |
| `save.` | `self.saving_throw_values` | `ABILITIES` | `save.wisdom` |

Notes:

- The suffix after the prefix must equal the enum's `.value` (e.g.
  `strength`, not `STRENGTH`). Failing to parse is a silent no-op.
- Any target not matching one of the above is silently ignored.
- Direct-attribute targets check `hasattr(self, attr)` before mutating,
  but all of them (`initiative`, `passive_perception`, `ac`) are now
  initialized in `Character.__init__`, so this is just a defensive
  guard rather than a gap.

### Symbolic values (resolved in `_resolve_modifier_value`)

| Value | Resolves to |
| --- | --- |
| `<int>` | itself |
| `"proficiency_bonus"` | `self.proficiency_bonus` |
| `"level"` | `self.level` |
| `"ability_modifier.<ability>"` | `self.ability_modifiers[ABILITIES(...)]` |

Any other string → `None`, which causes the modifier to be silently
skipped. This means typos in symbolic values fail closed.

### Application order

Called at the end of `update_automatic_values`, after `calculate_ac`, so:

- Base ability modifiers, saves, skills, AC (from armor/shield), and
  passive perception are already computed.
- Modifiers iterate **all features** (class + race + background feat).
  There is **no defined order between features** — the iteration order
  is dict-insertion order of `self.features`, which reflects
  `_merge_features`'s ordering (class → race → background feat).
- Modifiers stack: two `"op": "add"` modifiers on the same target
  accumulate; `"op": "set"` overwrites whatever came before it in the
  iteration. A passive `{ "target": "ac", "op": "add", ... }` modifier
  therefore stacks additively on top of whatever `calculate_ac` derived
  from the equipped armor/shield, and is recomputed fresh (not baked
  in) whenever `equip_armor`/`equip_shield` change and trigger
  `update_automatic_values` again.

### Recomputation caveat

`update_automatic_values` **rebuilds base values from scratch** each
time it runs (e.g. `calculate_ability_modifiers` overwrites the dict).
This means:

- Modifier effects are recomputed every time input state changes — no
  drift.
- Modifier effects are not permanently baked into base values — you can
  freely toggle modifiers by adding/removing features and re-running the
  pipeline (this is what `level_up` relies on).

### Adding a new modifier target

1. Decide whether it's a scalar attribute or a keyed collection.
2. Add it to `direct_targets` or `target_prefixes` in
   `Character._apply_single_modifier`.
3. Make sure `Character.__init__` initializes the underlying attribute
   or dict (this is how `ac` was made safe to target).
4. If the new target reads from a value not already in scope, extend
   `_resolve_modifier_value` too.

### Effects the modifier system deliberately can't express

- Advantage / disadvantage (e.g. Alert's "can't be surprised" clause).
- Resistances, immunities, damage-type interactions.
- Conditional triggers ("once per turn when you hit …").
- Reactions and reactions costs.
- Anything spellcasting-related.

These are kept as prose in `desc` fields; the plan (see
`PLAN_races_backgrounds.md`) is to enrich the vocabulary iteratively.
