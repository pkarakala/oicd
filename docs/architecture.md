# Architecture

_Independent model built from public information. Not affiliated with or endorsed by any company whose publications are cited._

```
references.bib ─┐                      docs/model_card.md (the spec: equations, hand cases)
catalog/products/*.toml ──► twin.catalog ──► twin.inference ──► evaluated graph (facts, derived,
catalog/geometry/*.toml ──┐   (validate)      (corners, MC,      checks, conflicts, support
profiles/*.json ──► schema │                  hypotheses)        matrix, tornado)
                    (Link)  │                                         │
                      │     │   physics: ring, wdm, bidi, mpi         │
                      ▼     │   system: rack, pod                     │
   checks ──► report ─┤     │   compute: ptc (ABFP), experiments      │
   sweep, tray,       │     ▼                                         ▼
   upstream, stats ───┴──► api.py, api_twin.py, api_physics.py (FastAPI, canonical JSON)
                                │            │            │
                    display.py (palette)   overlay.py (light, margins, heaters)
                                ▼
            web/ (React, three.js, Plotly): displays API responses only
            cli.py (uv run oicd ...), scripts/make_figures.py, scripts/make_twin_docs.py
```

**Engine (src/oicd).** `units` makes dB and dBm distinct types and OMA and average power distinct kinds; `schema` validates a Link (invalid physics is rejected, never given a verdict); `checks` return PASS, FAIL or NOT_EVALUATED with evidence; `report` builds the FeasibilityReport and power trace; `sweep`, `tray`, `upstream` and `statistics` are the brief 04 analyses. `physics` holds the microring, WDM, BiDi and MPI models of model card §12 and §13; `system` the reference rack and the pod; `compute` the photonic processor's ABFP data path (§15). Everything is pure and deterministic; random experiments take their seed.

**Twin (src/oicd/twin).** The catalog keeps facts (each with its exact quote, citation and class), SYNTHETIC assumptions (nominal, low, high, rationale), derived nodes (a named formula from `formulas`, never an evaluated string), checks and hypotheses. `inference` evaluates every node with an interval, classes derived values INFERENCE, compares checks (CONSISTENT, TENSION, CONFLICT), re-evaluates under each hypothesis for the support matrix, and computes tornado sensitivities. `physics` attaches engine evaluations to products; `overlay` maps results onto scene parts for the explorer.

**API.** FastAPI routes return canonical JSON; `web/openapi.json` and `web/src/api/schema.ts` are generated from it (`npm run gen:api`), and a test fails when they are stale. Colors and materials are served by `GET /display`, so the web decides no color.

**Explorer (web/).** A CAD shell: top bar, model tree, viewport (three.js through react-three-fiber, demand rendering, instanced parts, feature edges, AO, AgX tone mapping), Inspector and a dock of analyses. State lives in a zustand store with URL state and undo for design edits; server data in React Query. Playwright tests drive it end to end; Vitest covers the store, URL state and display helpers.

**Checks.** `uv run pytest -q` (with coverage in CI), `uv run ruff check .`, `uv run mypy` (strict), and in web/ `npm run typecheck`, `npm run test:unit`, `npm run build`, `npm run e2e`. Hand calculations in docs/hand_calcs/ use the standard library only and print every number the model card quotes.
