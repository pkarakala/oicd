# AGENTS.md

Rules for coding agents (and people) working in this repo. Most of the code was written by an AI coding assistant following these rules, with every change reviewed by the author.

## Rules

1. No unsourced numbers. A physical value carries a provenance class and a key from `references.bib`. If there is no source, it is `synthetic` with a one-line reason.
2. Units in types and names. `dB` and `dBm` are separate types; optical power is OMA or average, never mixed. Names end in the unit: `loss_db`, `wavelength_nm`.
3. `docs/model_card.md` is the spec. If code and card disagree, raise it; don't change the physics to make a test pass.
4. Checks are pure and deterministic and return PASS, FAIL or NOT_EVALUATED with the numbers behind them.
5. Expected test values come from the model card's hand calculations, not from running the code.
6. Keep diffs small and on one topic.
7. Write plainly: short sentences, no filler, no em dashes.

## Map

```
src/oicd/units.py, provenance.py   dB/dBm types, provenance classes
src/oicd/checks/                   electrical, wavelength, power budget
src/oicd/physics/                  MPI, BiDi, microring, WDM
src/oicd/system/                   rack and pod models
src/oicd/twin/                     catalog loader, inference graph, 3D overlay
src/oicd/compute/                  photonic tensor-core model
src/oicd/api*.py                   FastAPI used by the explorer
catalog/products/*.toml            sourced facts, one file per architecture
catalog/geometry/*.toml            3D scenes
docs/hand_calcs/                   standalone scripts behind the model card numbers
web/                               React + three.js explorer
```

## Commands

```bash
uv sync --all-groups
uv run ruff format . && uv run ruff check . && uv run mypy && uv run pytest -q
cd web && npm run gen:api && npm run typecheck && npm run test:unit
cd web && npm run e2e          # browser tests; rewrites docs/img/
uv run python scripts/make_twin_docs.py   # after editing catalog/
```

Run `npm run gen:api` after changing an API model (CI fails if `schema.ts` is stale), and `make_twin_docs.py` after changing anything in `catalog/`.
