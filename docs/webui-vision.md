# Web UI — Vision

This document elaborates [`vision.md`](./vision.md) into a concrete UI
specification: layout, screens, interactions, and rules for how each
piece of engine state is surfaced. It is prescriptive enough that a
frontend agent can build against it without having to re-derive intent
from the engine code.

Technical concerns (framework, API shape, deployment) live in
[`webui-architecture.md`](./webui-architecture.md). Backend gaps that
this UI depends on are catalogued in
[`../PLAN_webui_backend.md`](../PLAN_webui_backend.md).

## Design principles

1. **The character sheet is one page.** Everything the player looks at
   during play — abilities, HP, AC, skills, features, inventory —
   should be reachable without navigation. Modal/expanding panels for
   pickers (species, class, background, subclass, feats) are fine;
   route changes for the main sheet are not.
2. **Derived is decoration.** Any value the engine computes is rendered
   read-only and visually distinguished from editable inputs. The user
   never types "AC = 15" — they equip armor, and AC updates.
3. **Every mutation round-trips.** The frontend never guesses the
   result of an action; it sends the mutation, receives the fresh
   character snapshot, and re-renders. This keeps rule interpretation
   in one place (the engine) and lets the UI stay dumb.
4. **Show what's true now, hint at what unlocks later.** A level-3
   feature at level 2 is greyed with a "unlocks at 3" tooltip. A
   subclass dropdown before level 3 shows the requirement, not options.
5. **No hidden state.** Charges, remaining hit dice, temp HP, and
   choice picks are always visible on the sheet; the player never has
   to remember them.

## Screen inventory

For MVP, exactly two screens.

### 1. Character list ("home")

- Lists saved characters (name, class, level, race, background).
- "New character" button → opens the creation wizard (see below) then
  drops the user on the sheet.
- "Open" on a row → sheet screen.
- "Delete" on a row → confirmation dialog, then removed from disk.

This screen exists only because the browser reload otherwise loses
context. If a single-character mode is chosen for a first pass, replace
this with a redirect straight to the (only) sheet.

### 2. Character sheet

The main event. Layout described below.

There is intentionally **no** separate "combat mode" / "downtime" /
"level up" screen — every action is done inline on the sheet.

### Creation wizard (modal/inline, not a screen)

A short flow to fill the mandatory picks:

1. Name (text).
2. Class (dropdown, from `GET /catalog/classes`).
3. Race (dropdown).
4. Background (dropdown).
5. Ability scores (six number inputs, 3–20).
6. Background ASI distribution (see §Abilities).
7. Skill proficiency picks from the class (if the class grants any).

Skips: subclass (only unlocks at level 3+), inventory (seeded from
background), feats (only the background feat exists at level 1).

After confirm, the wizard POSTs one create-character call and drops
the user on the sheet.

## Sheet layout

A three-column layout on desktop, single column on mobile. Grouped
into six visual regions:

```
┌──────────────────────────── Header ────────────────────────────┐
│ [Name] [Class ▾] [Species ▾] [Subclass ▾] [Background ▾] Level │
├────────────────────────────────────────────────────────────────┤
│ Vitals: HP / Temp HP / Max HP · AC · Speed · Initiative        │
│         Prof bonus · Passive perception · Size                 │
│         Hit dice (d__ × remaining/total)                       │
│         [Short rest] [Long rest]                               │
├──────────────┬─────────────────────────────┬───────────────────┤
│ Abilities    │ Skills                      │ Saving throws     │
│ + saves      │ (18 rows, prof toggle)      │                   │
├──────────────┴─────────────────────────────┴───────────────────┤
│ Features (class · race · background · feats)                   │
├────────────────────────────────────────────────────────────────┤
│ Inventory · Equipped weapons · Armor · Shield                  │
├────────────────────────────────────────────────────────────────┤
│ Proficiencies: armor · weapons · tools · languages             │
└────────────────────────────────────────────────────────────────┘
```

Each region below describes its inputs, its read-only fields, and the
exact engine call each interaction triggers. All engine calls are
routed through the API described in
[`webui-architecture.md`](./webui-architecture.md#api-contract).

---

### Header — identity

| Field | Kind | Source | On change |
| --- | --- | --- | --- |
| Name | text input | `character.name` | `PATCH /character/{id}` (`set_name`), debounced 500ms |
| Class | dropdown | options from `GET /catalog/classes`, current from `character.class.id` | `PATCH /character/{id}/class` (`set_class`) — confirmation dialog: "This will re-derive features and reset invalid choices." |
| Species | dropdown | `GET /catalog/races` | `PATCH /character/{id}/race` (`set_race`) |
| Subclass | dropdown | `GET /catalog/subclasses?class_id=...`; **disabled** if `level < subclass_level`, tooltip explains when it unlocks | `PATCH /character/{id}/subclass` (`set_subclass`) |
| Background | dropdown | `GET /catalog/backgrounds` | `PATCH /character/{id}/background` (`set_background`); opens a modal to re-pick the ASI distribution and any newly-granted skill picks |
| Level | number input, 1–20, stepper | `character.level` | `PATCH /character/{id}/level` (`level_up`) — down-leveling is allowed (engine supports it via the same method) |

### Vitals

Two rows of numeric readouts + two buttons.

| Field | Kind | Source | Notes |
| --- | --- | --- | --- |
| Current HP | number input | `character.current_hp` | Clamped `[0, max_hp]` on send |
| Temporary HP | number input | `character.temporary_hp` | Independent of max; see backend §Temp HP |
| Max HP | read-only | `character.max_hp` | Recomputed from level + CON mod + class |
| AC | read-only | `character.ac` | |
| Speed | read-only | `character.speed` (feet) | |
| Initiative | read-only, signed | `character.initiative` | |
| Proficiency bonus | read-only, signed | `character.proficiency_bonus` | |
| Passive perception | read-only | `character.passive_perception` | |
| Size | read-only | `character.size` | |
| Hit dice | `dN × remaining/total` display + "Spend" button | `character.hit_die`, `hit_dice_remaining`, `hit_dice_total` | "Spend" calls `POST /character/{id}/hit-dice/spend` — engine decrements and returns die string; UI prompts the player for the rolled amount, then calls `heal` |
| Short rest button | button | — | `POST /character/{id}/rest/short` (`rest(SHORT_REST)`) |
| Long rest button | button | — | `POST /character/{id}/rest/long`; also resets current HP to max, clears temp HP, restores hit dice |

Convenience helpers on the HP row (optional but strongly recommended,
since they save the player from doing subtraction the engine already
knows how to do):

- **Damage** button + number → `POST /character/{id}/damage {amount}`
  (routes to `Character.take_damage`, which decrements temp first).
- **Heal** button + number → `POST /character/{id}/heal {amount}`.

### Abilities & saving throws

One row per ability (STR, DEX, CON, INT, WIS, CHA):

| Column | Kind | Source |
| --- | --- | --- |
| Ability name | label | — |
| Score | number input, 0–20 | `character.ability_points[ability]` (raw, pre-ASI) |
| Effective score | read-only | `ability_points + background_ability_bonuses.get(a, 0)` |
| Modifier | read-only, signed | `character.ability_modifiers[ability]` |
| Save bonus | read-only, signed | `character.saving_throw_values[ability]` |
| Save proficient? | dot / badge | `ability ∈ character.class.saving_throw_profs` |

On score change: `PATCH /character/{id}/ability/{ability} {value}`.

Below the abilities: a small **Background ASI** panel showing the
`ability_options` from the background and letting the player distribute
+2/+1 or +1/+1/+1. Sends to
`PATCH /character/{id}/background-ability-bonuses`. Show a validation
error inline if the engine returns 400 (rules: total 3, at most one 2,
subset of allowed abilities).

### Skills

18 skills in the fixed 2024 order, each with:

| Column | Kind | Source |
| --- | --- | --- |
| Proficient checkbox | tri-state? no — simple checkbox for now | `skill ∈ character.skill_profs` |
| Skill name | label | — |
| Ability tag | small label, e.g. `(DEX)` | `SKILL_TO_ABILITY[skill]` (surfaced in `to_dict`) |
| Bonus | read-only, signed | `character.skills[skill]` |
| Source badges | small icons | If the prof comes from class/background/player — surfaced via the three per-source sets |

The checkbox is only **user-editable** when the source is `player` (i.e.
not granted by class/background). If it's granted, the checkbox is
locked-on with a badge explaining the source.

On toggle: `PATCH /character/{id}/skill/{skill} {proficient: bool}` →
routes to `add_skill_prof` or `remove_skill_prof`.

### Features

A grouped, collapsible list. Groups: **Class**, **Race/Species**,
**Background feat**, and (later) **Feats**. Each entry:

- Name + type badge (`passive` / `active` / `choice`).
- Description text (`data.desc`), rendered as multi-paragraph markdown.
- If `active`: charges pill `remaining / max` + `Use` button
  (`POST /character/{id}/feature/{id}/use`). Greyed if `remaining == 0`.
  Hover tooltip shows recharge rules (`short rest` / `long rest` /
  none) parsed from `resource.recharge`.
- If `choice`: current pick (or "Not chosen") + dropdown to pick from
  `data.choice.source` catalog (fighting style, weapon mastery, …).
  Selection sends `PATCH /character/{id}/choice/{feature_id} {value}`.
  For weapon mastery specifically (vision §Class features), the UI
  shows N weapon slots (N derived from `data.choice.amount` at level)
  and each slot is a dropdown of the character's inventory weapons.
- If the feature unlocks at a higher level than current, render greyed
  with "Unlocks at level N" and no controls.

**Rest buttons** live in Vitals, not here — resting is per-character,
not per-feature.

### Inventory & equipment

Two side-by-side panels.

**Inventory** (all carried items):
- Table: name, kind (weapon/armor/gear/…), quantity, weight (per-unit +
  total), equip button (context-sensitive — only for weapons/armor).
- "Add item" combobox with catalog search
  (`GET /catalog/items?q=...`), calls `POST /character/{id}/inventory`.
- Row-level "Remove" decrements quantity, drops the row at 0.

**Equipped** (three slots):
- Weapons: list of currently equipped weapons with damage/property
  chips. "Unequip" per weapon. No slot cap enforced client-side
  (vision doesn't require it; backend allows it).
- Armor: single slot; dropdown of body-armor items in inventory,
  `equip_armor` on change, `unequip_armor` on clear.
- Shield: single slot; same, restricted to `shield` category.

Any equip/unequip triggers a full re-fetch (AC changes).

### Proficiencies panel

Static readouts, no interaction:

- Armor: `character.class.armor_profs` (badges: light/medium/heavy/shield).
- Weapons: `character.class.wep_profs` (simple/martial).
- Tools: `character.tool_profs` (from background).
- Languages: `character.languages` (from background).

---

## Interaction rules

- **Optimistic vs. pessimistic updates.** Default: pessimistic — send,
  wait, re-render. Numeric text inputs (name, ability scores, HP) may
  be locally-optimistic while typing, but the authoritative value on
  blur/debounce is the server response.
- **Debouncing.** Text inputs debounce 500ms. Number inputs on step
  (up/down) send immediately. Sliders (none in MVP) would debounce.
- **Error surfacing.** Any 4xx from the engine (e.g. invalid ability
  score, invalid ASI distribution, invalid subclass id) surfaces
  inline near the offending control with a plain-language message from
  the error body; the pre-error value is restored. 5xx surfaces as a
  toast.
- **Loading state.** The whole sheet has a subtle top-bar spinner
  while any request is in flight; individual controls do not each
  spin.
- **Empty states.** New character with no background → the Background
  ASI panel says "Pick a background to distribute ability bonuses."
  Inventory with nothing equipped → dashes in Armor/Shield slots.
- **Confirmation dialogs.** Only for destructive/expensive operations:
  changing class (may invalidate choices), changing race (rewrites
  species traits), deleting a character. Everything else is
  free-editing.

## What the UI deliberately does not do

- **No dice rolling.** The engine is deterministic; randomness stays in
  the player's hands (or an external roller). Hit dice, damage, and
  attack rolls are prompts, not automatic.
- **No spellcasting UI.** Out of scope until the engine supports it.
- **No character sharing / party view.** Single-user, single-character-at-a-time.
- **No PDF export, print styles, print layout.** Later.
- **No undo history.** State is committed on every mutation; the save
  file is authoritative.
- **No mobile-first design commitment.** Should not break on phones,
  but the target is desktop / tablet at the play table.

## Accessibility & style baseline

- All interactive controls have keyboard equivalents. Tab order is
  top-to-bottom, left-to-right within each region.
- All colors respect a WCAG AA contrast baseline. Never encode meaning
  in color alone (e.g. the "proficient" dot has a shape difference,
  not just a color).
- Font sizing scales with the browser's root font size.
- Numeric readouts use tabular-nums so single-digit / double-digit
  values line up.

Visual language, iconography, and exact palette are deferred to the
implementing agent; those choices should not require re-visiting this
document.
