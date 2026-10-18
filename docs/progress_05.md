# Progress: brief 05 (OICD v2 and the Lightmatter product twin)

Run of `briefs/05-v2-twin.md` on branch `v2`, started 2026-10-18. After any compaction, restart or pause: re-read the brief and this file, then continue from the first unchecked item. Each ticked item names the commit that contains it and the check results at that commit.

## Toolchain

| Tool | Version |
| --- | --- |
| uv | 0.13.1 (62faed335 2026-10-13 aarch64-apple-darwin) |
| Python | 3.12.4 |
| Node | v26.5.0 |
| npm | 11.17.0 |

Baseline before Phase 0 (brief 03 tree on `main`): pytest 147 passed, ruff check clean, ruff format clean.

## Phase 0: setup

- [x] 0.1 Commit the brief 03 work as "brief 03: report, API, 3D explorer" (421fc08)
- [x] 0.2 Commit the brief as "brief 05: add brief"; git status clean (5469737; also holds briefs/04-state-of-the-art-explorer.md, decision D05-1)
- [x] 0.3 Append the "Active run" and "Compact instructions" section to CLAUDE.md and commit — d0b203f; pytest 147 passed, ruff clean
- [x] 0.4 Create docs/progress_05.md with the uv, Python, Node and npm versions — d0b203f; pytest 147 passed, ruff clean

## Phase 1: review fixes R1 to R6 (brief 04 phase A)

- [x] 1.1 R1 engine: `above_threshold: bool` on every power_trace point, same ε rule as the verdict — phase 1 commit (hash in the next entry)
- [x] 1.2 R1 web: fiber tube and waterfall bars colored from that flag only — phase 1 commit (hash in the next entry)
- [x] 1.3 R1 test: losses [0.1, 0, 1.0, 0, 0.2] dB, R 4.7 dB, T01 otherwise → NOT_EXCLUDED, TP3 flag true, TP3 headroom within 1e-9 of 0 — phase 1 commit (hash in the next entry)
- [x] 1.4 R1 hypothesis property: verdict and TP3 flag always agree — phase 1 commit (hash in the next entry)
- [x] 1.5 R2: README bibliography wording, drop "realistic" — phase 1 commit (hash in the next entry)
- [x] 1.6 R3: threshold terms (penalties, reserve) in the TP3 / RX panel — phase 1 commit (hash in the next entry)
- [x] 1.7 R4: no change (recorded) — no change, as the brief says
- [x] 1.8 R5: selection by stable identity, so inserting a connector never moves an open panel — phase 1 commit (hash in the next entry)
- [x] 1.9 R6 card §3: threshold_dbm = S_RX + ΣΠ + R, headroom_db(plane), lower/upper clearance; M_net decides; headroom at TP3 equals M_net — phase 1 commit (hash in the next entry)
- [x] 1.10 R6 card §4: fiber as the two §2 segments (2 × 0.0004 dB) — phase 1 commit (hash in the next entry)
- [x] 1.11 Card uses ≥ and ≤, never >= or <=; 0.4 dB/km note kept until Phase 5 — phase 1 commit (hash in the next entry)
- [x] 1.12 Card §7 row per change, dated 2026-10-18 — phase 1 commit (hash in the next entry)
- [x] 1.13 Phase 1 checks green and commit — b6e9c6e; pytest 149 passed, ruff check and format clean, npm run build ok, typecheck ok, e2e 1 passed

## Phase 2: engine features (brief 04 phases B, C, D, D2)

- [x] 2a.1 Card §8 design-space sweep with hand cases (1.0, 0) +0.4992; (2.0, 0) −0.5008; (0, +1) +2.4992; slopes −1 and +1 — phase 2 commit
- [x] 2a.2 src/oicd/sweep.py `sweep(link, x_path, x_values, y_path, y_values) -> SweepResult`, NumPy-vectorized, max 201×201 — phase 2 commit
- [x] 2a.3 POST /sweep; tests: hand cases, slopes, 422 unknown path, 422 oversized grid — phase 2 commit
- [x] 2b.1 Card §9 multi-lane tray; hand case 8 lanes, lane 5 patch 2.0 dB → −0.5008, deciding lane 5, EXCLUDED — phase 2 commit
- [x] 2b.2 src/oicd/tray.py, POST /evaluate_tray; tests: hand case, property (adding a lane never raises tray margin) — phase 2 commit
- [x] 2c.1 Card §10 upstream chain (Milestone 2), hand cases N = 16, 17, 18, max fan-out 17 — phase 2 commit
- [x] 2c.2 src/oicd/upstream.py `derive_tp2(chain)` with itemized trace, `max_fanout(...)` — phase 2 commit
- [x] 2c.3 Report gains optional upstream section; POST /evaluate accepts a fixed TP2 or a chain; tests — phase 2 commit
- [x] 2d.1 Card §11 statistical budget and yield, with the "why"; hand case σ_total 0.34641, z 1.44107, yield 0.92522, 3σ margin −0.54003 — phase 2 commit
- [x] 2d.2 src/oicd/statistics.py `analytic_yield`, `monte_carlo_yield` (seeded Generator, 10^6 samples within 0.002) — phase 2 commit
- [x] 2d.3 POST /yield labeled "statistical, assumption-dependent"; never changes the worst-case verdict; tests — phase 2 commit
- [x] 2.4 docs/hand_calcs scripts for §8 to §11 — phase 2 commit
- [x] 2.5 Phase 2 checks green and commit — 832ea3e; pytest 206 passed, ruff check and format clean, npm run build ok, typecheck ok, e2e 1 passed

## Phase 3: validation against standards

- [x] 3.1 Open and cite welch2023_3dj_baseline, johnson2025_3dj_mpidgd, dawe2026_3dj_er199, simms2026_3dj_tt, bhatt2016_mpi, anslow2017_drrefl, bhatt2001_bidixtalk — phase 3 commit
- [x] 3.2 Card §12 draft IEEE 802.3dj 200G DR budget; profiles/ieee_dr_200g.json (PROPOSED_STANDARD); test NOT_EXCLUDED and |M| < 1e-9 — phase 3 commit
- [x] 3.3 `max_channel_il(n_refl_45_35, n_refl_55_45)` from Table 180-12; tests (0,0) 3.0, (0,6) 2.9, (2,3) 2.8, (4,4) 2.5, (5,0) 2.5, (4,8) and (6,0) not supported — phase 3 commit
- [x] 3.4 src/oicd/physics/mpi.py worst-case bound; published example n = 2, 4, 6 → 0.8142, 1.4378, 2.3137 dB; card says bound is conservative vs IEEE 1e-6 allocation — phase 3 commit
- [x] 3.5 src/oicd/physics/bidi.py reflection crosstalk; IL 7, RL 12 → 1.6509 dB; BiDi extension (INFERENCE) IL 3, RL 15.5, I 0 → 0.2514 dB; I 25 → 0.000772 dB; RL ≥ IL + 5 dB rule — phase 3 commit
- [x] 3.6 Hand-calc scripts and tests for all of the above — phase 3 commit
- [x] 3.7 Phase 3 checks green and commit — 83416c0; pytest 238 passed, ruff check and format clean; no web changes

## Phase 4: twin foundation

- [ ] 4.1 PEER_REVIEWED and THIRD_PARTY source classes (citation key required); card §7 row
- [ ] 4.2 Catalog file format: catalog/products/<product>.toml and catalog/geometry/<scene>.toml
- [ ] 4.3 Fact verification: every Appendix A fact checked against its opened source, exact quote stored, verified flag set
- [ ] 4.4 src/oicd/twin/catalog.py: Pydantic models and validation (unique ids, cites in references.bib, inputs resolve, no cycles)
- [ ] 4.5 src/oicd/twin/formulas.py: pure typed functions with units in names, each unit-tested
- [ ] 4.6 src/oicd/twin/inference.py: nominal/lo/hi (corners; Monte Carlo above 12 interval parents, flagged), class, derivation strings; checks CONSISTENT/TENSION/CONFLICT; hypotheses and support matrix; tornado
- [ ] 4.7 Tests: catalog validation, toy graph with hand values, support matrix, tornado
- [ ] 4.8 Phase 4 checks green and commit

## Phase 5: device and link physics

- [ ] 5.1 Open and cite hu2025_arxiv, geravand2025_mrm, decort2011, frey2006_dndt, xu2014_thermo, sun2015_nature, bogaerts2012_mrr, itut_g652_2024 (and an open source for the crosstalk form)
- [ ] 5.2 Card §13 microring and WDM link physics (f0, FSR, FWHM, periodic Lorentzian, lifetime caveat, thermal tuning)
- [ ] 5.3 Crosstalk penalty (INFERENCE): −10·log10(1 − k·X), k = 1 NRZ, 3 PAM4; alternative 10·log10(1 + X)
- [ ] 5.4 Design window (SYNTHETIC rules): Q_min, Q_max
- [ ] 5.5 Thermal tuning requirement, barrel shifting, heater power
- [ ] 5.6 Guide grid (INFERENCE) and aliasing analysis
- [ ] 5.7 BiDi link model in bidi.py (per-direction budget, diplexer IL, reflection crosstalk, MPI, containment, G.652 fiber loss); §4 note cites itut_g652_2024
- [ ] 5.8 Hand-calc script with every brief value; tests and properties
- [ ] 5.9 Phase 5 checks green and commit

## Phase 6: product twins and the reference rack

- [ ] 6.1 Card §14: twin method, reference rack, every derived formula
- [ ] 6.2 Passage L20 catalog and checks
- [ ] 6.3 Passage M1000 catalog and checks
- [ ] 6.4 Passage L200/L200X catalog and checks
- [ ] 6.5 16λ BiDi link (EVK50, OFC 2026) with H_fsr18 and H_fsr32
- [ ] 6.6 Guide family (Guide, Guide 1, Guide DR) and the Guide DR fan-out run
- [ ] 6.7 OCP trays with H_dir / H_agg and height hypotheses
- [ ] 6.8 Pod example (CPX, HOTI26)
- [ ] 6.9 Reference rack OICD-R64: frame, trays, links, worst path, reference-plane hypotheses, rack yield
- [ ] 6.10 src/oicd/system/rack.py and pod.py; single-tier topology radix vs OCP vision
- [ ] 6.11 Hand-calc scripts and tests with every brief value
- [ ] 6.12 Phase 6 checks green and commit

## Phase 7: API

- [ ] 7.1 GET /catalog, GET /catalog/{product}, POST /inference/{product}, GET /geometry/{scene}
- [ ] 7.2 POST /ring, /wdm/grid, /wdm/crosstalk, /bidi/link, /mpi, /rack, /pod, /ptc/simulate; existing endpoints kept
- [ ] 7.3 web/src/api/schema.ts from OpenAPI via openapi-typescript (npm run gen:api), regenerated in CI
- [ ] 7.4 Tests per endpoint with hand values; 422 on invalid physics; deterministic JSON
- [ ] 7.5 Phase 7 checks green and commit

## Phase 8: CAD-grade 3D explorer

- [ ] 8.1 Stack additions installed (tailwindcss, zustand, react-query, react-resizable-panels, cmdk, radix, lucide-react, postprocessing, three-mesh-bvh, elkjs, vitest, testing-library)
- [ ] 8.2 Layout: top bar, model tree, viewport, Inspector, bottom dock tabs, Cmd/Ctrl+K palette
- [ ] 8.3 Viewport: perspective/orthographic, ViewCube, keys 1-4, F, Shift+F, damped controls
- [ ] 8.4 CAD rendering: feature edges, N8AO, SMAA, tone mapping, Lightformer studio, contact shadows, mm grid and scale bar, gradient background, selective bloom
- [ ] 8.5 PBR materials (silicon, substrate, copper, steel, aluminium, glass fibre, polymer)
- [ ] 8.6 Tools: hover/select outlines, Esc; section view with caps; exploded view; measure tool; undo/redo
- [ ] 8.7 Semantic zoom Rack → Tray → Engine → PIC → Ring with transitions
- [ ] 8.8 Physics overlays from the API (false-color light paths, pulses, BiDi ghost, margin colormap, heater overlay, leader labels)
- [ ] 8.9 Geometry from catalog/geometry via the API, dims_class in the Inspector, SCHEMATIC tint toggle
- [ ] 8.10 Inference tab (elkjs graph, derivation chain, hypothesis toggle, support matrix, tornado, conflicts)
- [ ] 8.11 Brief 04 views: Design space, Tray, Upstream, Yield, Export report; footer captions
- [ ] 8.12 Performance: demand frameloop, instancing, merged geometry, BVH, code-split scenes, dev fps meter
- [ ] 8.13 Ease of use: guided tours, shortcut sheet, tooltips, URL state, PNG export 2×, themes, ARIA and focus
- [ ] 8.14 Scenes 1 to 7 (rack, switch tray, XPU tray, L20 + BiDi link, M1000, L200, Guide family) with Spec sheet, Inference and Physics tabs
- [ ] 8.15 Playwright suite and screenshots; Vitest for store and URL state
- [ ] 8.16 Phase 8 checks green and commit

## Phase 9: photonic processor

- [ ] 9.1 Open ahmed2025_nature (and basumallik2022_abfp); card §15 with the A9 facts and derived values
- [ ] 9.2 Processor catalog entry with checks and conflicts
- [ ] 9.3 src/oicd/compute/ptc.py ABFP data path with the hand cases
- [ ] 9.4 Seeded experiments: error vs length, gain and ENOB; ABFP vs global scale; 3-layer MLP accuracy vs G
- [ ] 9.5 Stretch: per-weight-cell optical power under two laser-mapping hypotheses
- [ ] 9.6 POST /ptc/simulate and scene 8
- [ ] 9.7 Phase 9 checks green and commit

## Phase 10: refinement, figures, paper, docs

- [ ] 10.1 .github/workflows/ci.yml; strict type check on src/oicd with no errors; pre-commit config
- [ ] 10.2 CLI: oicd evaluate | sweep | fanout | twin <product> | rack
- [ ] 10.3 Coverage ≥ 95% on src/oicd; uncovered lines listed
- [ ] 10.4 scripts/make_figures.py (11 figures, PDF and PNG in docs/figures/)
- [ ] 10.5 docs/twin/<product>.md, docs/lightmatter_public_spec_sheet.md, docs/demo_script.md
- [ ] 10.6 docs/paper/main.md
- [ ] 10.7 README, docs/architecture.md, CITATION.cff
- [ ] 10.8 Remove the "Active run" section from CLAUDE.md; all checks one final time
- [ ] 10.9 docs/run_summary_05.md (final summary), printed

## Check log

| Phase | Commit | pytest | ruff check | ruff format | web build | typecheck | e2e | vitest |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | d0b203f | 147 passed | clean | clean | n/a | n/a | n/a | n/a |
| 1 | b6e9c6e | 149 passed | clean | clean | ok | ok | 1 passed | n/a |
| 2 | 832ea3e | 206 passed | clean | clean | ok | ok | 1 passed | n/a |
| 3 | 83416c0 | 238 passed | clean | clean | n/a | n/a | n/a | n/a |
