# Contributing

Corrections are the most useful contribution. If a number is wrong, a source is misread, or the physics is off, please say so.

## Report a mistake

Open an issue with the "Wrong number or physics" template. Include the value, where you saw it (explorer screen, twin page or file), and what it should be with a source. No code needed.

## Set up

```bash
git clone https://github.com/pkarakala/oicd && cd oicd
uv sync --all-groups
cd web && npm install --legacy-peer-deps && cd ..
./scripts/dev.sh        # API on :8000, explorer on :5173
```

## Fix a fact

Facts live in `catalog/products/*.toml`. Each one has a value, unit, exact quote, citation key and provenance class:

```toml
[[fact]]
id = "fau.il_reinsertion_max"
value = 1.5
unit = "dB"
quote = "A demonstrated insertion and re-insertion loss of less than 1.5 dB"
cite = "vendor_pr_fau"
source_class = "vendor_claim"
verified = true
```

Add the source to `references.bib` if it's new, then regenerate the twin pages with `uv run python scripts/make_twin_docs.py`.

## Change the physics

1. Update `docs/model_card.md` first: equation, reference plane, and a worked case.
2. Add the hand calculation to `docs/hand_calcs/`.
3. Write the test from that number, then the code.

## Before a PR

```bash
uv run ruff format . && uv run ruff check . && uv run mypy && uv run pytest -q
cd web && npm run gen:api && npm run typecheck && npm run test:unit
```

See [AGENTS.md](AGENTS.md) for the rules and a map of the code.
