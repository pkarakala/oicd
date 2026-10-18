Brief 04: correctness fixes, codebase refinement and a state-of-the-art 3D explorer. First save this whole message verbatim as briefs/04-state-of-the-art-explorer.md. Then read CLAUDE.md, docs/model_card.md, docs/decisions_pending.md (including the "Review by session oicd-69" section) and briefs/03-report-api-3d.md. Work through phases A to F in order. After each phase, run its checks and fix any failure before starting the next. Stop only after phase F, then summarize. Do not commit.

Hard rules for the whole brief:
- The Python engine is the only place physics is computed. The web app never computes dB, margins, thresholds or verdicts, and never compares a value against 0 or against a threshold to decide anything. It displays what the API returns.
- No new physics. Do not change docs/model_card.md except where phase A says so. Anything that would need a new equation, parameter or pass rule goes into docs/decisions_pending.md as a question for Pranav, not into code.
- Every new physical value carries Provenance (CLAUDE.md rule 1). Unsourced means SYNTHETIC with a rationale.
- Keep checks green at every phase: uv run pytest -q, uv run ruff check ., uv run ruff format --check ., and in web/: npx tsc --noEmit, npm run build, npx playwright test.
- Log every judgment call in docs/decisions_pending.md under a new "Brief 04" heading (question, choice, why).

PHASE A: correctness fixes from the brief 03 review (R1, R2, R3, R5)
- R1: add above_threshold: bool to each report TracePoint, computed in Python as headroom_db >= -EPSILON_DB (the same ε as the margin pass rule). The web uses only this flag for green/red, in both the fiber tube and the waterfall. Magnitude can still come from headroom_db. Add a pytest boundary test: losses [0.1, 0, 1.0, 0, 0.2] dB, launch 0 dBm, S -6 dBm, R 4.7 dB. Expected: verdict NOT_EXCLUDED, and the TP3 point has above_threshold True. Add a hypothesis property: for any valid link, the power-budget check status is PASS iff the TP3 point has above_threshold True.
- R2: README: replace "Only sources that were actually opened are listed there" with "Each entry's note records whether it was read and its information class." Remove the word "realistic".
- R3: the TP3 / RX engine provenance panel also lists the threshold terms (every penalties[*] record and reserve), under a "Threshold terms" heading.
- R5: select by stable identity (input_path for loss elements, "TP2"/"TP3" for planes), so adding a connector never moves an open panel to a different component.
- R6 and model card style: do not edit the card. Write proposed wording in docs/decisions_pending.md for: (a) the clearance definitions, (b) threshold = S + ΣΠ + R, with headroom shown for display using the same ε as M_net, (c) "≥" and capitals in the brief 03 §3 line and §7 rows. Pranav will apply it.
Check: all checks above pass, and git diff on docs/model_card.md is empty for this phase.

PHASE B: engine and API refinement (no physics changes)
- Add GET /profiles, which lists the available profile names.
- Add POST /sweep: a Link, a target input path (channel[i].loss_max, tx.launch_oma_min, rx.sensitivity_oma_max, penalties[i].value or reserve), start, stop and step (at most 201 points). It returns, for each value, margin_db and verdict, computed by calling evaluate() on an edited copy of the Link. Validate the path and range and return 422 on bad input. It is pure and deterministic.
- Add a version field to the report JSON (report_schema_version = "1") so the web can detect a mismatch.
- Tests: sweep endpoints equal evaluate() at the same values; margin is monotone non-increasing in any loss (hypothesis); bad path → 422; too many points → 422.
- Type the API with response models so /docs shows real schemas.
Check: all checks pass.

PHASE C: web architecture and quality
- Split the bundle: lazy-load the Plotly chart and the 3D scene (React.lazy + Suspense) so the first paint does not wait for them. Report the before and after bundle sizes.
- Add vitest with unit tests for linkEdits.ts and format.ts (pure functions only).
- Add an ESLint flat config (typescript-eslint strict, react-hooks) and make npm run lint pass.
- Generate the TypeScript report and Link types from the FastAPI OpenAPI schema (openapi-typescript) instead of hand-written types.ts. Add npm run gen:types, and a test that fails if the generated file is stale.
- Accessibility: every control is keyboard reachable, has a visible focus ring and a label; the scene has a text alternative listing each component with its loss and headroom (from the API).
Check: all checks pass, plus npm run lint and npx vitest run.

PHASE D: state-of-the-art 3D explorer (visual and interaction, no new physics)
- Detailed procedural models, still schematic and labeled as such:
  - The TX/RX optical engine as a co-packaged optics package: substrate, package lid, PIC die and heat spreader, with a cutaway toggle that shows the die.
  - The FAU as a glass V-groove block with a lid and a fiber ribbon.
  - The patch connector as an MPO-style ferrule pair with guide pins.
  - The fiber as a jacketed tube with a visible core when hovered.
- Light flow: animated pulses travel along the fiber, TX to RX. Pulse brightness at each segment comes from the API's power_dbm via a fixed display mapping documented in code. Pulses stop at a component whose above_threshold is False and turn red there. Add a pause button and respect prefers-reduced-motion.
- Rendering: physically based materials, an HDR environment bundled locally (no CDN fetch at runtime), soft shadows, bloom on the light pulses (@react-three/postprocessing), and tone mapping. The frame rate must stay smooth on a laptop: adaptive DPR and on-demand rendering when idle.
- Camera: smooth animated transitions between presets (overview, TX, RX, plus one per component on double-click), and a "guided tour" button that flies TX → RX with a caption per component (name, loss_db, headroom_db, source class).
- Floating labels: try drei Html or Billboard + Text again for an in-scene verdict badge and per-component labels. If it still fails under React 19 StrictMode, keep the DOM overlay and record the exact error in decisions_pending.
- Sweep view: from any slider, a "sweep" button calls POST /sweep and draws margin against that input in a Plotly line chart, with the NOT_EXCLUDED/EXCLUDED boundary taken from the API's verdicts (not computed in TS) and the current value marked.
- Scenarios: compare two links side by side (A/B) with both badges and both waterfalls; save and load scenarios as Link JSON files (download/upload, validated by POST /evaluate). Undo/redo for edits; the URL hash stores the current scenario so a link can be shared.
- Keep the permanent footer caption: "Schematic, not to scale. Values synthetic unless cited. PASS means not excluded by modeled constraints."
Check: all checks pass. Extend web/tests/smoke.spec.ts or add specs for: tour runs end to end; the sweep chart appears with ≥ 2 points; A/B shows two verdicts; undo restores NOT_EXCLUDED after the +1 dB patch edit; the boundary profile from phase A shows no red anywhere under a NOT_EXCLUDED badge. Save screenshots to docs/img/explorer.png (overview) and docs/img/explorer-tour.png.

PHASE E: developer experience
- .github/workflows/ci.yml: uv sync, pytest, ruff, then web install, lint, tsc, vitest, build, and Playwright (Chromium) with both servers started by the Playwright config. Do not push; just write the file.
- scripts/dev.sh: print clear URLs, check that ports 8000 and 5173 are free first, and keep the Ctrl+C cleanup.
- A Makefile or justfile with: dev, test, lint, fmt, e2e, types.
Check: all checks pass; bash -n scripts/dev.sh.

PHASE F: README and handoff
- README: update the screenshot(s), describe the new controls (tour, sweep, A/B, scenarios, undo), the new endpoints, and how to run each check. Keep the limitations section and add "animations and models are illustrative". Keep "Code implemented with an AI coding assistant; models, physics and design decisions by Pranav."
- docs/decisions_pending.md: list every brief 04 choice, plus a "Physics questions for Pranav" list for anything that would need model card changes (for example the Milestone 2 upstream TX chain, multi-lane/WDM, temperature drift, statistical budgets).

Final summary: what you built per phase, the check output for each phase, the bundle sizes before and after, every assumption, and anything in the model card that is wrong or ambiguous.
