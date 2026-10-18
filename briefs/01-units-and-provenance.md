# Brief 01: units and provenance

Paste everything below the line into Claude CLI from the repo root, after `CLAUDE.md` and `docs/model_card.md` are in place.

---

Read CLAUDE.md and docs/model_card.md. Implement only `src/oicd/units.py`, `src/oicd/provenance.py` and their tests. Nothing else.

units.py:
- `DBm` and `DB` as distinct immutable types (frozen dataclasses or Pydantic models) wrapping a float.
- Allowed: `DBm - DB -> DBm`, `DBm + DB -> DBm`, `DBm - DBm -> DB`, `DB + DB -> DB`. Every other combination raises `TypeError`, including `DBm + DBm`.
- `PowerKind` enum: `OMA`, `AVERAGE`. An `OpticalPower` holds a `DBm` and a `PowerKind`; arithmetic between different kinds raises `UnitMismatchError`.
- Conversions: `mw_to_dbm`, `dbm_to_mw`, `avg_to_oma(p_avg: OpticalPower, er_db: DB) -> OpticalPower` using OMA = 2·P_avg·(ER−1)/(ER+1).
- `delta_lambda_nm(lambda_nm, delta_f_ghz)` using Δλ ≈ λ²Δf/c with c = 299792458 m/s.

provenance.py:
- `SourceClass` enum: `PUBLISHED_SPEC`, `PROPOSED_STANDARD`, `VENDOR_CLAIM`, `SYNTHETIC`, `INFERENCE`.
- `Provenance(source_class, citation_key: str | None, rationale: str)`. `citation_key` is required unless `SYNTHETIC` or `INFERENCE`, and must exist in references.bib (parse keys with a regex; no bibtex dependency).
- `Quantity[T]`: a value plus its Provenance.

Tests (pytest + hypothesis):
- Every allowed and forbidden operation above.
- `mw_to_dbm(1) == 0`, `mw_to_dbm(100) == 20` within 1e-12.
- Round trip mW → dBm → mW for random positive powers.
- Model card T08: P_avg = 0 dBm, ER = 4 dB → OMA ≈ −0.650 dBm (tolerance 1e-3).
- 200 GHz at 1310 nm ≈ 1.145 nm (tolerance 1e-3).
- Provenance rejects an unknown citation key and a VENDOR_CLAIM without a key.

Done when `uv run pytest -q` and `uv run ruff check .` pass. Then stop and summarize what you built, what you assumed, and anything in the model card you think is wrong.
