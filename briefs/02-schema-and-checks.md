Brief 02: schema, constraint registry and the three checks. First save this whole message verbatim as briefs/02-schema-and-checks.md. Then read CLAUDE.md and docs/model_card.md and implement only what follows. No report.py, no profiles, no plots (that is brief 03).

0. pyproject.toml: add [tool.ruff] line-length = 100 and [tool.ruff.lint] select = ["E", "F", "I", "B", "UP"], so lint rules live in the repo. Fix anything this flags in existing code.

1. src/oicd/schema.py: frozen Pydantic v2 models. Every physical number is a Quantity carrying Provenance.
   - ElectricalInterface: modulation (Literal "NRZ", "PAM4"), symbol_rate_gbd > 0, lanes >= 1, fec: str, provenance.
   - Transmitter: name, electrical, center_wavelength_nm: Quantity[float] > 0, wavelength_tolerance_nm: Quantity[float] >= 0, launch_oma_min: Quantity[OpticalPower] (at TP2).
   - Receiver: name, electrical, passband_min_nm and passband_max_nm (Quantity[float], 0 < min < max), sensitivity_oma_max: Quantity[OpticalPower] (at TP3).
   - LossElement: name, loss_max: Quantity[DB] with loss >= 0.
   - Penalty: name, value: Quantity[DB] >= 0.
   - Link: tx, rx, channel: tuple[LossElement, ...], penalties: tuple[Penalty, ...] (default empty), reserve: Quantity[DB] >= 0.
   Invalid physics (model card T12) raises a ValueError at construction.

2. src/oicd/registry.py: ConstraintId (StrEnum). Evaluated: ELECTRICAL_MATCH, WAVELENGTH_CONTAINMENT, OPTICAL_POWER_BUDGET. Not evaluated: BER, TDECQ, DISPERSION, REFLECTIONS_MPI, THERMAL, RELIABILITY. Expose EVALUATED and NOT_EVALUATED as frozensets, and EPSILON_DB = 1e-9.

3. src/oicd/checks/{__init__,electrical,wavelength,power_budget}.py: pure functions, each taking a Link and returning a frozen CheckResult(constraint: ConstraintId, status: Status, evidence: dict[str, float | str], message: str), with Status PASS, FAIL or NOT_EVALUATED.
   - electrical: compare modulation, symbol_rate_gbd, lanes and fec. FAIL lists every mismatched field, and the evidence still reports all four.
   - wavelength: PASS iff [λ − δ, λ + δ] ⊆ [min, max]. Evidence includes lower_clearance_nm and upper_clearance_nm (negative when outside).
   - power_budget: exactly model card §3, worst case, OMA only. Sum losses with sum(..., start=DB(0.0)). Evidence: total_loss_db, p_tp3_dbm, sensitivity_dbm, penalties_db, reserve_db, margin_db, epsilon_db. PASS iff margin >= -EPSILON_DB. A TX/RX kind mismatch raises UnitMismatchError (T07).

4. Tests: one test per model card case T01 to T12, named test_T01_... and so on, with expected values copied from the card, not computed by the code. Add a hypothesis property for T05 (adding any loss >= 0 never raises the margin). Use the worked example (§4) as a shared fixture, with all values SYNTHETIC and a rationale.

Done when uv run pytest -q and uv run ruff check . pass. Then stop and summarize: what you built, every assumption, and anything in the model card that is wrong or ambiguous. Do not commit.
