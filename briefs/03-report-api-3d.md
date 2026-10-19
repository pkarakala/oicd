Brief 03: report, API and the interactive 3D link explorer. First save this whole message verbatim as briefs/03-report-api-3d.md. Then read CLAUDE.md and docs/model_card.md. Work through phases A to E in order. After each phase, run its checks and fix any failure before starting the next. Stop only after phase E, then summarize. Do not commit.

Hard rule for the whole brief: the Python engine is the only place physics is computed. The web app never computes dB, margins or verdicts; it only displays what the API returns.

PHASE A: model card updates (Pranav authorizes exactly these edits)
- T07 expected: "raises UnitMismatchError at schema construction (bad input, not a feasibility verdict)".
- T12: "negative loss, 0 nm wavelength, passband min >= max, NaN/inf rejected at schema with ValueError; ER <= 0 dB rejected by avg_to_oma".
- T06: "report and check evidence name the penalty".
- §3 wavelength: "PASS iff both clearances >= -ε_nm, ε_nm = 1e-9 nm".
- §4: add "Wavelength and electrical (synthetic): TX 1310 ± 2 nm, RX passband 1300 to 1320 nm, PAM4, 106.25 GBd, 1 lane, RS(544,514)."
- §7, two rows dated 2026-10-18: "Unit-kind mismatch raises instead of FAIL | a mismatch is invalid input, not a verdict; rule 5 applies to valid links | return FAIL: hides input bugs as physics" and "Wavelength pass rule clearance >= -1e-9 nm | float edge test found -2.27e-13 nm on an edge that is exact on paper | exact containment: random failures at real edges".
Check: git diff shows only docs/model_card.md changed in this phase.

PHASE B: report and profiles
- src/oicd/report.py: evaluate(link) -> FeasibilityReport (frozen Pydantic). Fields: link_name; results (the three CheckResults); not_evaluated (one CheckResult with Status.NOT_EVALUATED for each NOT_EVALUATED ConstraintId, with a one-line reason); verdict ("NOT_EXCLUDED" if no FAIL, else "EXCLUDED"); inputs (each physical input: path, value, unit, source_class, citation_key, rationale); power_trace (ordered list: TP2, then the cumulative OMA after each loss element, ending at TP3, each with element name and power_dbm); threshold_dbm = sensitivity + penalties + reserve.
- to_json(): deterministic (sorted keys, fixed float repr).
- profiles/worked_example.json: model card §4, all SYNTHETIC with rationale. src/oicd/profiles.py: load_link(path) -> Link.
- Tests: T13 (every input lists its SourceClass), T14 (two runs give identical JSON), T15 (the not-evaluated list is exactly BER, TDECQ, dispersion, reflections/MPI, thermal, reliability), a power_trace test (worked example ends at -4.0008 dBm), and a JSON round trip of the profile.
Check: uv run pytest -q, uv run ruff check .

PHASE C: API
- uv add fastapi uvicorn; uv add --dev httpx.
- src/oicd/api.py: FastAPI app with POST /evaluate (Link JSON -> report JSON), GET /profiles/{name} (from profiles/), and GET /health. Allow CORS for http://localhost:5173 only. Invalid physics returns 422 with the validation message.
- Tests with TestClient: the worked example returns margin_db 0.4992 within 1e-9; negative loss returns 422; an unknown profile returns 404.
Check: uv run pytest -q; uv run uvicorn oicd.api:app starts and /health returns ok.

PHASE D: web/ interactive 3D explorer
Stack: Vite, React, TypeScript (strict), three, @react-three/fiber, @react-three/drei, react-plotly.js with plotly.js-dist-min. Use current stable versions.
- Scene: a schematic 3D model of the link laid out left to right. TX optical engine (package on a substrate), TX fiber-array unit, fiber as a tube along a smooth curve, patch connector, fiber, RX fiber-array unit, RX engine. One 3D object per element in the report's power_trace, so the scene comes from the data, not hard-coded.
- Encoding: the fiber tube color shows local power headroom above threshold_dbm (green above, red below, using the power_trace values from the API). Each component's emissive intensity scales with its share of total loss. A floating verdict badge shows NOT_EXCLUDED or EXCLUDED and margin_db.
- Interaction: orbit, zoom and pan; camera presets (overview, TX close-up, RX close-up); hover tooltip per component (name, loss dB, source class, citation key); click to select and open a side panel with the full provenance.
- Controls panel: a slider for every loss element, TX launch OMA, RX sensitivity, each penalty and the reserve, plus an "add connector" button. Every change POSTs the edited Link to /evaluate (debounced 150 ms), and the scene, badge and chart update from the response.
- 2D power waterfall (Plotly), synced with the 3D scene: OMA at each plane in power_trace, a horizontal threshold line, and the margin annotated at TP3. Hovering a bar highlights the matching 3D component, and the reverse.
- Show the three check results and the not-evaluated list in a collapsible panel.
- A permanent footer caption: "Schematic, not to scale. Values synthetic unless cited. PASS means not excluded by modeled constraints."
- Loads profiles/worked_example via GET /profiles/worked_example on start.
Checks: npm run build and npx tsc --noEmit pass. Add one Playwright test (web/tests/smoke.spec.ts) that starts from the worked example, sees NOT_EXCLUDED, raises the patch connector loss by 1 dB, sees EXCLUDED with margin -0.5008, and saves a screenshot to docs/img/explorer.png.

PHASE E: run script and README
- scripts/dev.sh starts the API (port 8000) and the web app (port 5173) together, and stops both on Ctrl+C.
- README.md: what OICD is (two sentences); the screenshot; how to run (uv sync, cd web && npm install, ./scripts/dev.sh); the engine pipeline in one diagram (profiles -> schema -> checks -> report -> API -> 3D explorer); limitations (synthetic values, single lane, no BER prediction, not an OCP or IEEE compliance tool); citations from references.bib; and "Code implemented with an AI coding assistant; models, physics and design decisions by Pranav."

Final summary: what you built per phase, every assumption, the check output for each phase, and anything in the model card that is wrong or ambiguous.
