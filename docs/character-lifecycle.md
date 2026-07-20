# Character lifecycle

Everything the caller does goes through the `Character` class
(`src/sheet_project/engine/character.py`). This document walks through
its lifecycle: construction, derivation, and each mutation method.

## Constructor

```python
Character(
    name: str,
    class_name: str,
    background_name: str | None = None,
    race_name: str | None = None,
)
```

The constructor performs, in order:

1. **Load content** via the three loaders. `background` and `race` are
   `None` if their name argument is `None` (backwards compatible).
2. **Initialize input state:** `ability_points` (all zero),
   `background_ability_bonuses` (empty), `current_hp = 0`, empty
   `choices`.
3. **Initialize derived state** to zero-valued dicts:
   `ability_modifiers`, `saving_throw_values`, `skills`.
4. **Set the three skill-prof source sets**:
   - `skill_profs_from_class` — empty (populated when class grants skill
     choices; today classes carry none).
   - `skill_profs_from_background` — seeded from `self.background.skill_profs`.
   - `skill_profs_from_player` — empty; grown via `add_skill_prof`.
   - `skill_profs` — the union, recomputed by
     `_recompute_skill_prof_union`.
5. **Populate background-derived collections**:
   `tool_profs`, `languages`.
6. **Race-driven attributes** (with fallbacks when race is `None`):
   - `speed` → `race.speed` or `30`
   - `size` → `race.size` or `"medium"`
   - `creature_type` → `race.creature_type` or `"humanoid"`
7. **Merge features** into `self.features` via `_merge_features`.
8. **Initialize equipment state**: `inventory` (empty list),
   `equipped_weapons` (empty list), `equipped_armor` / `equipped_shield`
   (`None`), `ac = 10`. Then seeds `inventory` from the background's
   `equipment` ids via `_seed_inventory_from_background()` — this only
   populates `inventory`, it never auto-equips anything.
9. **Recompute all derived state** via `update_automatic_values()`.
10. **Initialize per-feature state** via `_initialize_features()`
    (sets `ActiveFeature.max_use` and `remaining_use`).

## Feature merging

`_merge_features()` returns a single flat dict:

```python
{
    **self.character_class.features,        # class first
    **(self.race.features if self.race else {}),   # race second (overrides class on id clash)
    **(                                            # background feat last (overrides both)
        {self.background.feat.id: self.background.feat}
        if self.background else {}
    ),
}
```

If ids ever collide, later entries silently win. In current content, all
ids are unique.

## `update_automatic_values` — the recompute pipeline

Called by the constructor and by every mutation that changes input state.

```python
def update_automatic_values(self):
    self._recompute_skill_prof_union()
    self.calculate_ability_modifiers()
    self.calculate_saving_throw_values()
    self.calculate_skills()
    self.calculate_ac()
    self.calculate_passive_perception()
    self.apply_modifiers()
```

Step-by-step:

1. **`_recompute_skill_prof_union`** — `skill_profs = class ∪ background ∪ player`.
2. **`calculate_ability_modifiers`** — for each ability:
   `score = ability_points[a] + background_ability_bonuses.get(a, 0)`
   then `ability_modifiers[a] = (score - 10) // 2`.
   Also sets `self.initiative = ability_modifiers[DEXTERITY]` (before
   modifiers).
3. **`calculate_saving_throw_values`** — `mod[a] + proficiency_bonus` if
   `a` is in `character_class.saving_throw_profs`, else just `mod[a]`.
4. **`calculate_skills`** — for each skill: `ability_modifiers[ability_of(skill)]
   + (proficiency_bonus if skill ∈ skill_profs else 0)`.
5. **`calculate_ac`** — derives `self.ac` from `equipped_armor` /
   `equipped_shield` (see [features-and-modifiers.md](./features-and-modifiers.md)
   for the DEX-cap rules and shield stacking).
6. **`calculate_passive_perception`** — `13 + skills[PERCEPTION]`.
   > Note: the D&D formula is `10 + Perception modifier`. The engine
   > uses `13`, which appears to be a bug/typo; recorded here as
   > current behavior.
7. **`apply_modifiers`** — iterates every feature's `data["modifiers"]`
   list and mutates the derived fields, including `ac` (see
   [features-and-modifiers.md](./features-and-modifiers.md)). Since this
   runs after `calculate_ac`, any `ac` modifier stacks on top of the
   armor/shield-derived base.

## Public mutation methods

All of these end by calling `update_automatic_values()` (except the ones
that touch state which does not affect derived values).

| Method | Effect |
| --- | --- |
| `set_ability(ability, value)` | Rejects out-of-range values (< 0 or > 20) silently. Otherwise stores the raw score and recomputes. |
| `add_skill_prof(skill)` / `remove_skill_prof(skill)` | Mutates only `skill_profs_from_player`, then recomputes. |
| `set_hp(hp)` | Clamped to `0 ≤ hp ≤ max_hp`. Does *not* trigger recompute (HP is not derived). |
| `use_feature(feature_id)` | Delegates to the feature's `.use()` if it's an `ActiveFeature`; returns `True`/`False`. |
| `rest(rest_type: RESTTYPE)` | Calls `.rest(rest_type)` on every feature. `ActiveFeature.rest` reads its `resource.recharge` map. |
| `level_up(new_level)` | Rebuilds `character_class` at the new level, re-merges features, recomputes, and re-initializes ActiveFeature charges (see below). |
| `set_background_ability_bonuses(bonuses)` | Validates the distribution (see below) and recomputes. Returns `True` on success, `False` on rejection. |
| `add_item(item_or_id, quantity=1)` / `remove_item(item_id, quantity=1)` | Mutate `inventory` (stacking by id via `InventoryEntry.quantity`). Does *not* recompute — inventory contents don't affect derived stats until equipped. |
| `equip_weapon(weapon_id)` / `unequip_weapon(weapon_id)` | Move a `Weapon` already in `inventory` into/out of `equipped_weapons`. No AC effect, so no recompute. |
| `equip_armor(armor_id)` / `unequip_armor()` | Set/clear `equipped_armor` (must be `LIGHT`/`MEDIUM`/`HEAVY` category) and recompute. |
| `equip_shield(armor_id)` / `unequip_shield()` | Set/clear `equipped_shield` (must be `SHIELD` category) and recompute. |

### Equipment methods

- `add_item`/`remove_item` accept either an id string (resolved via
  `EquipmentResolver`) or an already-resolved `Weapon`/`Armor`/`Item`
  instance. Equipping requires the item to already be in `inventory` —
  `equip_weapon`/`equip_armor`/`equip_shield` look it up with
  `_find_in_inventory` and silently no-op if it isn't found (or if the
  category doesn't match the slot).
- Only `equip_armor`/`unequip_armor` and `equip_shield`/`unequip_shield`
  trigger `update_automatic_values()`, since only those affect `ac`
  (see `calculate_ac` in [features-and-modifiers.md](./features-and-modifiers.md)).

### `level_up` semantics

```python
def level_up(self, new_level):
    self.level = new_level
    self.character_class = self.cl_loader.load_class(self.level)
    self.features = self._merge_features()
    self.update_automatic_values()
    self._initialize_features()
```

- Class content is reloaded (new features unlock).
- `_initialize_features` calls `ActiveFeature.set_values(level)` which
  **preserves already-consumed charges**: if the max increases by N, the
  remaining pool grows by up to N without ever exceeding the new max.
  See `ActiveFeature.set_values` in
  `src/sheet_project/engine/features/active_feature.py`.

### `set_background_ability_bonuses` validation

The distribution must satisfy **all** of:

- Keys ⊆ `background.ability_options` (only the 3 allowed abilities).
- Every value is in `{1, 2}`.
- Values sum to exactly `3`.
- At most one `2`.

This admits exactly the two 2024 rulebook distributions: `+2/+1` and
`+1/+1/+1`. Fails silently (returns `False`) on any violation.

Requires a background to be set; returns `False` otherwise.

## Read-only properties

```python
@property
def proficiency_bonus(self) -> int:
    return 2 + (self.level - 1) // 4

@property
def max_hp(self) -> int:
    return self.character_class.hitpoints.calculate(
        self.level,
        self.ability_modifiers,
    )
```

Both are computed on access; there's no cached copy. `max_hp` reads
`ability_modifiers`, which is why `set_ability` re-runs
`update_automatic_values`.

## Ordering hazards worth knowing

- **`initiative` is set inside `calculate_ability_modifiers`** and *then*
  possibly increased by `apply_modifiers` (e.g. Alert). If you add
  another step that reads `initiative`, put it after `apply_modifiers`.
- **`passive_perception` runs before `apply_modifiers`**, so any
  modifier targeting `skill.perception` would land *after* passive
  perception is computed. If you add a `skill.perception` modifier, be
  aware passive perception won't reflect it unless the order is
  changed. (Modifiers can target `passive_perception` directly.)
- **`_initialize_features` runs after `update_automatic_values`**, so
  active features see the recomputed level but not any modifier-mutated
  values (which is fine — modifiers today only touch scalar stats).
