# OICD: Open Interconnect Co-Design

Physics-grounded feasibility engine for optical AI-accelerator interconnects. Author and owner: Pranav. This file sets the rules for any coding agent working in this repo.

## Non-negotiable rules

1. **No fabricated numbers.** Every physical parameter in code, profiles, tests or docs carries a `Provenance`: one of `published_spec`, `proposed_standard`, `vendor_claim`, `synthetic`, `inference`, plus a citation key from `references.bib` (or `synthetic` with a one-line rationale). If a value has no source, it is `synthetic`. Never invent a datasheet value.
2. **Explicit units in names and types.** `dBm` and `dB` are distinct types; adding two `dBm` values must be impossible. Optical power fields declare `PowerKind.OMA` or `PowerKind.AVERAGE`; mixing kinds raises an error. Field names carry units: `loss_db`, `wavelength_nm`, `symbol_rate_gbd`.
3. **The model card is the spec.** `docs/model_card.md` defines reference planes, equations and expected test values. Code implements it; it does not change it. If the model card looks wrong, stop and say so instead of "fixing" the physics.
4. **Pure, deterministic functions.** No global state, no randomness, no I/O inside checks. Same inputs, same outputs, bit for bit.
5. **Three-state results.** Every constraint returns `PASS`, `FAIL` or `NOT_EVALUATED` with numeric evidence. A PASS means "not excluded by the modeled constraints", never "the link works".
6. **Tests first, against hand calculations.** Expected values in tests come from the model card, not from running the code.
7. **Small diffs.** One brief per session. Do not build ahead of the current brief (no dashboard, NetworkX or LLM search until asked).

## Stack

Python 3.12, `uv`, Pydantic v2, NumPy, pytest, hypothesis (property tests), ruff. Visualization later: Plotly for 2D, Three.js (react-three-fiber) for 3D.

## Layout

```
src/oicd/units.py        # dB/dBm types, conversions, PowerKind
src/oicd/provenance.py   # Provenance model, citation keys
src/oicd/schema.py       # Transmitter, Receiver, LossElement, Link
src/oicd/registry.py     # constraint IDs
src/oicd/checks/         # electrical.py, wavelength.py, power_budget.py
src/oicd/report.py       # FeasibilityReport
profiles/                # synthetic JSON profiles
docs/model_card.md       # the physics spec (written by Pranav)
references.bib           # verified sources only
tests/
```

## Commands

`uv run pytest -q` · `uv run ruff check .` · `uv run ruff format .`
