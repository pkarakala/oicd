# Contributing

1. No unsourced numbers. Every physical value carries a provenance class and a citation from `references.bib`; anything without a source is `synthetic` with a one-line reason.
2. Units live in types and names. `dB` and `dBm` are distinct types; optical power is OMA or average, never mixed. Names carry units (`loss_db`, `wavelength_nm`).
3. `docs/model_card.md` is the spec. Code implements it; if the card looks wrong, fix the card first.
4. Checks are pure and deterministic, and return PASS, FAIL or NOT_EVALUATED with evidence. PASS means "not excluded", not "works".
5. Test expectations come from hand calculations in the model card, never from running the code.

```bash
uv run pytest -q && uv run ruff check . && uv run mypy
cd web && npm run typecheck && npm run test:unit
```
