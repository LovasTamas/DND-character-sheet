# Web UI — Architecture

This document is the technical companion to
[`webui-vision.md`](./webui-vision.md). It covers stack choices, the
HTTP/JSON contract between browser and engine, project layout,
deployment, and testing.

Backend gaps that this architecture depends on are enumerated in
[`../PLAN_webui_backend.md`](../PLAN_webui_backend.md). Content and
interaction rules live in [`webui-vision.md`](./webui-vision.md). The
engine's data model is documented in
[`architecture.md`](./architecture.md) and
[`character-lifecycle.md`](./character-lifecycle.md).

## Stack

| Layer | Choice | Rationale |
| --- | --- | --- |
| Engine | Existing `sheet_project.engine` (Python 3.11+) | Unchanged. Data-first, no framework, no ORM. |
| API | **FastAPI** + Uvicorn | Native Python, no runtime cost to the engine, auto-generated OpenAPI schema (which the frontend can codegen types from), Pydantic models validate request bodies without duplicating the engine's rule checks. Flask + `flask-openapi` would also work; FastAPI is picked because it gives the OpenAPI schema for free. |
| Persistence | JSON files on disk (`data/characters/*.json`) | Matches the engine's data-first bent, zero-dep. A SQLite/Postgres migration is a single-module change later. |
| Frontend framework | **React + TypeScript**, scaffolded with Vite | Widest agent/tool coverage, TS gives type-safe API bindings, Vite dev server has good HMR. Alternative: SvelteKit for less boilerplate; React chosen for familiarity and ecosystem depth. |
| Frontend state | React Query (TanStack Query) for server state + React `useState` for local form state | Server state is the character JSON returned by every mutation — React Query cache invalidation on mutation is the exact pattern the vision requires ("every mutation round-trips"). Redux/MobX are overkill. |
| Styling | Tailwind CSS | Utility classes keep the sheet's dense readouts consistent without a component library. Optional: shadcn/ui for a small set of primitives (dialogs, dropdowns). |
| Build / bundling | Vite | Fast dev iteration, tiny prod bundles, works with any router. |
| Package management | `pip` / `uv` for backend, `pnpm` for frontend | `pnpm` for content-addressed store; either is fine. |

**Non-choices** (deliberately not picked, and why):
- **No SSR / Next.js.** The sheet is a stateful client-side app; SSR
  buys nothing and complicates deployment.
- **No GraphQL.** The API is small and mutation-driven; REST is a
  better fit.
- **No WebSocket / SSE.** Vision is single-user, single-tab. Pushing
  updates would only be needed for real-time multi-user, which is out
  of scope.
- **No monorepo tooling (Nx/Turbo).** One backend, one frontend, one
  repo, no cross-project workspaces needed.

## Repository layout

Additions to the existing repository (nothing existing moves):

```
DND-character-sheet/
├── data/
│   └── characters/            # (new) persisted character save files
├── docs/
│   ├── webui-vision.md        # what the UI is
│   ├── webui-architecture.md  # this file
│   └── webui-api.md           # (optional split) machine-readable OpenAPI export
├── src/
│   └── sheet_project/
│       ├── engine/            # unchanged
│       ├── api/               # (new) FastAPI app
│       │   ├── __init__.py
│       │   ├── main.py        # FastAPI app + router registration
│       │   ├── routes/        # one module per resource (character, catalog, rest, ...)
│       │   ├── schemas.py     # Pydantic request/response models
│       │   ├── serializers.py # Character/Feature/Weapon/... → dict helpers if not on the engine itself
│       │   └── deps.py        # dependency-injected persistence, character-by-id lookup
│       └── tests/
│           ├── engine_tester.py  # existing
│           └── api_tester.py     # (new) requests-driven smoke of the HTTP surface
└── webui/                     # (new) frontend project (Vite + React + TS)
    ├── index.html
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.ts
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx
    │   ├── api/               # generated / hand-rolled fetch layer
    │   ├── pages/
    │   │   ├── CharacterList.tsx
    │   │   └── Sheet.tsx
    │   ├── components/
    │   │   ├── Header.tsx
    │   │   ├── Vitals.tsx
    │   │   ├── Abilities.tsx
    │   │   ├── Skills.tsx
    │   │   ├── Features.tsx
    │   │   ├── Inventory.tsx
    │   │   └── Proficiencies.tsx
    │   └── types.ts           # mirrors the Character JSON shape
    └── public/
```

Nothing in `src/sheet_project/engine/` is imported by `webui/`
directly; the browser never sees Python. The engine and the API layer
share a process; the frontend is a separate build served either by
FastAPI's `StaticFiles` in production or Vite's dev server in
development.

## API contract

All routes are prefixed `/api/v1`. All request/response bodies are
`application/json`.

### Character JSON shape

The response body returned by every character read/mutation is:

```jsonc
{
  "id": "b1c9…",
  "name": "Tomi",
  "level": 5,

  "class": { "id": "fighter", "name": "Fighter", "hit_die": "d10",
             "saving_throw_profs": ["strength", "constitution"],
             "wep_profs": ["simple", "martial"],
             "armor_profs": ["light", "medium", "heavy", "shield"] },
  "race":       { "id": "human", "name": "Human", "size": "medium", "speed": 30, "creature_type": "humanoid" } ,
  "background": { "id": "guard", "name": "Guard", "ability_options": ["strength", "wisdom", "constitution"] },
  "subclass":         { "id": null, "name": null },
  "subclass_options": [ { "id": "champion", "name": "Champion" } ],
  "subclass_unlock_level": 3,

  "abilities": {
    "strength":     { "score": 15, "effective": 17, "modifier": 3, "save": 5, "save_proficient": true  },
    "dexterity":    { "score": 14, "effective": 14, "modifier": 2, "save": 2, "save_proficient": false },
    "constitution": { "score": 14, "effective": 14, "modifier": 2, "save": 4, "save_proficient": true  },
    "intelligence": { "score": 10, "effective": 10, "modifier": 0, "save": 0, "save_proficient": false },
    "wisdom":       { "score": 12, "effective": 13, "modifier": 1, "save": 1, "save_proficient": false },
    "charisma":     { "score":  8, "effective":  8, "modifier": -1,"save": -1,"save_proficient": false }
  },
  "background_ability_bonuses": { "strength": 2, "wisdom": 1 },

  "skills": [
    { "id": "perception", "ability": "wisdom", "bonus": 4,
      "proficient": true, "sources": ["background"] },
    ...
  ],
  "skill_prof_choices_available": { "class": 0, "player_picked": 2 },

  "vitals": {
    "current_hp": 44, "max_hp": 44, "temporary_hp": 0,
    "ac": 18, "speed": 30, "initiative": 2,
    "proficiency_bonus": 3, "passive_perception": 14, "size": "medium",
    "hit_die": "d10", "hit_dice_total": 5, "hit_dice_remaining": 5
  },

  "features": [
    { "id": "second_wind", "name": "Second Wind", "kind": "active",
      "source": "class", "desc": "…", "activation": "bonus_action",
      "max_use": 3, "remaining_use": 2,
      "recharge": { "short_rest": -1, "long_rest": -1 },
      "unlocked": true, "unlock_level": 1 },
    { "id": "fighting_style", "name": "Fighting Style", "kind": "choice",
      "source": "class", "desc": "…",
      "choice": { "source": "fighting_styles", "amount": 1 },
      "chosen_value": "defense",
      "unlocked": true, "unlock_level": 1 },
    { "id": "alert", "name": "Alert", "kind": "passive",
      "source": "background", "desc": "…",
      "unlocked": true, "unlock_level": 1 },
    ...
  ],

  "inventory": [
    { "item": { "id": "chain_mail", "name": "Chain Mail", "kind": "armor",
                "category": "heavy", "weight": 55 },
      "quantity": 1 },
    ...
  ],
  "equipped_weapons":  [ { "id": "longsword", "name": "Longsword", ... } ],
  "equipped_armor":     { "id": "chain_mail", "name": "Chain Mail", ... },
  "equipped_shield":    { "id": "shield", "name": "Shield", "ac_bonus": 2 },

  "proficiencies": {
    "armor":     ["light", "medium", "heavy", "shield"],
    "weapons":   ["simple", "martial"],
    "tools":     ["thieves_tools"],
    "languages": ["common", "elvish"]
  }
}
```

The exact field names are the authoritative contract; the frontend's
TypeScript `Character` type mirrors them. The engine's
`Character.to_dict()` (backend plan §2) produces this shape.

### Endpoints

Grouped by resource. Every mutating endpoint returns `200 OK` with the
full updated character body. All errors return
`{ "error": { "code": "...", "message": "...", "field": "..." } }`.

#### Catalog (read-only, cacheable)

| Method | Path | Returns |
| --- | --- | --- |
| GET | `/api/v1/catalog/classes` | `[ { id, name } ]` |
| GET | `/api/v1/catalog/races` | `[ { id, name } ]` |
| GET | `/api/v1/catalog/backgrounds` | `[ { id, name } ]` |
| GET | `/api/v1/catalog/subclasses?class_id=fighter` | `[ { id, name } ]` |
| GET | `/api/v1/catalog/feats` | `[ { id, name } ]` |
| GET | `/api/v1/catalog/weapons?q=long` | `[ { id, name, category, type } ]` |
| GET | `/api/v1/catalog/armors?q=` | `[ { id, name, category } ]` |
| GET | `/api/v1/catalog/items?q=` | `[ { id, name, kind } ]` |
| GET | `/api/v1/catalog/fighting-styles` | `[ { id, name, desc } ]` — content TBD by backend plan followups |

Cache-Control: `public, max-age=3600`. Catalogs never change at runtime.

#### Characters

| Method | Path | Body | Engine call |
| --- | --- | --- | --- |
| GET | `/api/v1/characters` | — | List saved character summaries (from `data/characters/*.json`) |
| POST | `/api/v1/characters` | `{ name, class_name, race_name?, background_name? }` | `Character(...)` + `save(...)` |
| GET | `/api/v1/characters/{id}` | — | Load + `to_dict()` |
| DELETE | `/api/v1/characters/{id}` | — | Delete save file |

#### Character mutations

All under `/api/v1/characters/{id}`.

| Method | Path | Body | Engine call |
| --- | --- | --- | --- |
| PATCH | `/name` | `{ name }` | `set_name` |
| PATCH | `/class` | `{ class_name }` | `set_class` |
| PATCH | `/race` | `{ race_name \| null }` | `set_race` |
| PATCH | `/background` | `{ background_name \| null }` | `set_background` |
| PATCH | `/subclass` | `{ subclass_id \| null }` | `set_subclass` |
| PATCH | `/level` | `{ level }` | `level_up` |
| PATCH | `/ability/{ability}` | `{ value }` | `set_ability` |
| PATCH | `/background-ability-bonuses` | `{ "strength": 2, "wisdom": 1 }` | `set_background_ability_bonuses` |
| PATCH | `/skill/{skill}` | `{ proficient: bool }` | `add_skill_prof` / `remove_skill_prof` |
| PATCH | `/hp` | `{ value }` | `set_hp` |
| PATCH | `/temporary-hp` | `{ value }` | `set_temporary_hp` |
| POST | `/damage` | `{ amount }` | `take_damage` |
| POST | `/heal` | `{ amount }` | `heal` |
| POST | `/hit-dice/spend` | — | `spend_hit_die` → returns `{ die: "d10", remaining: 4 }` **plus** the fresh character body |
| POST | `/rest/short` | — | `rest(SHORT_REST)` |
| POST | `/rest/long` | — | `rest(LONG_REST)` — also resets HP/temp/hit dice per backend plan §5 |
| POST | `/feature/{feature_id}/use` | — | `use_feature` |
| PATCH | `/choice/{feature_id}` | `{ value }` | Writes into `character.choices` via the `ChoiceFeature`'s `choose` |
| POST | `/inventory` | `{ item_id, quantity? }` | `add_item` |
| DELETE | `/inventory/{item_id}` | `{ quantity? }` (query) | `remove_item` |
| POST | `/equipped/weapons` | `{ weapon_id }` | `equip_weapon` |
| DELETE | `/equipped/weapons/{weapon_id}` | — | `unequip_weapon` |
| PUT | `/equipped/armor` | `{ armor_id \| null }` | `equip_armor` / `unequip_armor` |
| PUT | `/equipped/shield` | `{ shield_id \| null }` | `equip_shield` / `unequip_shield` |

**Design rule.** If a UI action doesn't map to a single existing engine
method (with at most argument shaping), that's a signal the engine is
missing a capability — file it in
[`../PLAN_webui_backend.md`](../PLAN_webui_backend.md), don't paper
over it in a route handler.

### Errors

Response status uses standard HTTP semantics:

| Status | When |
| --- | --- |
| `400 Bad Request` | Rule violation the engine detected (invalid ability, invalid ASI distribution, invalid subclass id, HP out of range). |
| `404 Not Found` | Unknown character id, unknown catalog id. |
| `409 Conflict` | Attempted to equip an item not in inventory, wrong slot category. |
| `500` | Uncaught exception (engine bug). |

Body shape (always the same):

```json
{ "error": { "code": "invalid_ability_score",
             "message": "Ability score must be between 0 and 20.",
             "field": "value" } }
```

`code` is a stable string suitable for i18n or frontend switch; the
frontend must not parse `message`.

## Serialization boundary

- **`Character.to_dict()`** (backend plan §2) is the *only* engine-side
  serializer. Everything the API returns runs through it (plus tiny
  wrappers for catalog lists).
- **Pydantic models** in `src/sheet_project/api/schemas.py` describe
  the *request* bodies (validation + OpenAPI docs). They do **not**
  describe responses — response shape is whatever `to_dict()` produces,
  documented as a `Character` TypedDict in `webui-vision.md` and this
  file.
- The frontend has a hand-maintained `types.ts` that mirrors the
  response shape. If desired, `openapi-typescript-codegen` can generate
  request types from FastAPI's OpenAPI export; the response type stays
  hand-maintained because FastAPI's inferred type for a `dict` return
  is unhelpful.

## Persistence

- One JSON file per character at `data/characters/{id}.json`.
- File name = character id = UUID v4 assigned on create.
- Contents = `Character.to_save_dict()` output — input state only, no
  derived fields (see backend plan §8).
- Write pattern: write to a temp file, then `os.replace` to the final
  name (atomic on POSIX). No file locking — vision is single-user.
- List endpoint reads the directory and pulls the minimum fields
  needed for the character-list screen (`name`, `class_name`, `level`,
  `race_name`, `background_name`) without hydrating a full `Character`.

Migration to SQLite/Postgres later is a single-module swap: replace
`persistence.py`'s `save`/`load`/`list` with DB equivalents; the API
layer never sees the difference.

## Cross-cutting concerns

### CORS

Development: `webui/` runs on `http://localhost:5173` (Vite default),
API on `http://localhost:8000`. FastAPI's `CORSMiddleware` allows the
Vite origin in dev only. In prod, the API serves the built frontend
from the same origin, so CORS is not needed.

### Auth

None in MVP. The API binds to `127.0.0.1` by default, and the vision
is local single-user. If exposed to a LAN, add HTTP Basic behind a
`--enable-auth` flag as a follow-up.

### Concurrency

None. FastAPI's default async event loop is fine; character mutations
are per-file and serialized by the OS. If two tabs edit the same
character simultaneously, last-write-wins — acceptable for MVP.

### Logging

Standard Python `logging`. `INFO` for request start/finish, `WARNING`
for 4xx, `ERROR` with stacktrace for 5xx. No structured logging in
MVP.

### Configuration

Twelve-factor:
- `DATA_DIR` (defaults to repo `data/`).
- `CHARACTERS_DIR` (defaults to `DATA_DIR/characters`).
- `API_HOST`, `API_PORT`.
- `CORS_ORIGINS` (dev only).

Loaded from env vars via `pydantic-settings`.

## Deployment

Two supported modes:

### Dev

Two processes:

```bash
# backend
PYTHONPATH=src uvicorn sheet_project.api.main:app --reload

# frontend
cd webui && pnpm dev
```

Vite proxies `/api/*` to `http://localhost:8000` (see `vite.config.ts`).

### Prod (single-user, local)

Build the frontend, mount it as static files:

```bash
cd webui && pnpm build       # → webui/dist/
PYTHONPATH=src uvicorn sheet_project.api.main:app --host 127.0.0.1
```

FastAPI serves `/` from `webui/dist/` via `StaticFiles`, `/api/v1/*`
from the API routers. One process, one port. A tiny launcher script
(`bin/dnd-sheet`) that runs `uvicorn` + opens the browser is a nice
touch but not required.

Packaging into a single executable (PyInstaller, Nuitka) is out of
scope; the launcher script is sufficient.

## Testing

### Backend

- **Engine tests:** existing `engine_tester.py` continues to be the
  smoke source of truth for engine correctness.
- **API tests:** new `api_tester.py` (or migrate to `pytest`
  eventually) exercises each route via FastAPI's `TestClient`:
  - Create character → assert 201, id present.
  - GET character → shape matches contract.
  - Each mutation → assert response body reflects the change.
  - Each rule-violation → assert `400` with expected `error.code`.
- **Contract test:** the API test suite asserts the OpenAPI schema
  matches a committed snapshot (`docs/webui-api.md` or
  `openapi.json`). Any accidental contract change fails loudly.

### Frontend

- **Type-only:** `tsc --noEmit` in CI to guarantee `types.ts` matches
  the current API responses (via a small fixture-based check).
- **Component tests:** Vitest + React Testing Library for the four or
  five stateful components (Vitals, Abilities, Skills, Features).
- **E2E:** Playwright, one happy-path spec that creates a Fighter,
  levels to 3, equips chain mail + shield, spends a hit die,
  short-rests, long-rests. This one test guards the whole
  vision.md flow.

## Follow-ups this architecture unlocks

- **Auth + multi-user:** slot into `deps.py`'s character-lookup
  dependency; no route changes.
- **Real-time collaboration:** add SSE endpoint that pushes the
  post-mutation character body; frontend swaps React Query cache
  entries. Only needed for multi-user.
- **PDF export:** dedicated `/api/v1/characters/{id}/export.pdf`
  route using `weasyprint` against a print-styled render of the sheet.
- **Rule content expansion** (subclasses, spells, feats at level 4/8):
  data-only in the engine, no API changes required as long as they
  fit the existing `Feature` / `ChoiceFeature` shapes.
