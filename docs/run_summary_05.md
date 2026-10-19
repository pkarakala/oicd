# Brief 05 run summary: OICD v2 and the product twin

_Independent reconstruction from public information. Not affiliated with or endorsed by Lightmatter. Product names belong to their owners._

Branch `v2`, 17 commits on top of `main` (nothing pushed, `main` untouched). Every number below carries its class in the twin, the explorer and the docs; this summary repeats the class where it matters.

## What was built, phase by phase

- **Phase 0, setup.** Brief 03 and the brief committed, CLAUDE.md's active-run section, docs/progress_05.md with tool versions (uv 0.13.1, Python 3.12, Node 26.5, npm 11.17).
- **Phase 1, review fixes R1 to R6.** `above_threshold` on every trace point with the verdict's ε (the explorer colors only from that flag), threshold and headroom defined in model card §3, selection by stable key, threshold terms at TP3.
- **Phase 2, engine features.** Design-space sweep with the engine's 0 dB contour (§8), multi-lane trays (§9), the upstream laser chain with TP2 derived and maximum fan-out (§10: N = 17 passes, N = 18 fails at −0.2034 dB), statistical yield with seeded Monte Carlo (§11: 0.92522).
- **Phase 3, validation.** Draft IEEE 802.3dj 200G DR budget as a profile (PROPOSED_STANDARD; M_net 0 on paper, about −4.4e-16 in floats, NOT_EXCLUDED), Table 180-12, the worst-case MPI bound (0.8142, 1.4378, 2.3137 dB against the source's 0.81, 1.44, 2.31) and BiDi reflection crosstalk (1.6509 dB against ≈ 1.65), with its diplexer extension labelled INFERENCE.
- **Phase 4, twin foundation.** SourceClass gained PEER_REVIEWED and THIRD_PARTY; a TOML catalog with validation, a typed formula registry, an inference engine with intervals, checks, hypotheses, support matrix and tornado; 506 facts verified by opening their sources (462 by exact quote).
- **Phase 5, device and link physics.** Model card §13: periodic Lorentzian rings, WDM crosstalk penalty (INFERENCE, with the alternative form), SYNTHETIC design window, thermal tuning with barrel shifting, the interleaved Guide grid (INFERENCE), aliasing and the worst-channel rule, and the BiDi link model.
- **Phase 6, product twins and the reference rack.** Catalog graphs and physics for M1000, L200, L20, the 16λ BiDi link, Guide family, OCP trays, the pod example and OICD-R64 (§14).
- **Phase 7, API.** Catalog, inference, geometry, ring, WDM, BiDi, MPI, rack and pod endpoints; generated TypeScript types with a staleness test.
- **Phase 8, CAD-grade explorer.** A new web app on React 19, three.js and react-three-fiber with a CAD shell (top bar, model tree, viewport, Inspector, dock, command palette), 10 geometry scenes from the API down to µm and nm levels, sections with hatched stencil caps, exploded views, a snapping measure tool, guided tours with catalog captions, physics overlays served by GET /overlay (false-color light, pulses at the engine's linear power, BiDi ghosts, margin colormaps, heater power), every color served by GET /display, and the brief 04 views (design space, tray, upstream, yield). Playwright and Vitest suites.
- **Phase 9, photonic processor.** Model card §15, the catalog graph with hypotheses for the ADC range and the laser mapping, an independent ABFP data path (`src/oicd/compute/ptc.py`), seeded experiments, POST /ptc/simulate, scene 8 and a simulator panel.
- **Phase 10, refinement.** CI workflow, mypy --strict clean, pre-commit, the `oicd` CLI, 98 % coverage, 11 figures, generated twin pages and spec sheet, the demo script, the paper draft, README, architecture page, CITATION.cff.

## Commits

```
7002ed4 brief 05 phase 10: CI, strict types, CLI, coverage, figures, twin docs, paper, README
cbeeeec brief 05: progress after phase 9
d4eeeef brief 05 phase 9: photonic processor twin, ABFP data path and experiments
935e262 brief 05: progress after phase 8
58b63de brief 05 phase 8: CAD-grade 3D explorer
a78fb8f brief 05 phase 7: API for the twin, physics and geometry, and generated TypeScript types
f64cddd brief 05: progress after phase 6
24aa45a brief 05 phase 6: product twins and the reference rack
9e8da7d brief 05 phase 4: verified public facts catalog
5558b7e brief 05 phase 5: microring, WDM and BiDi link physics
3b4f339 brief 05 phase 4: twin catalog, formulas and inference engine
83416c0 brief 05 phase 3: validation against draft IEEE 802.3dj DR, MPI and BiDi crosstalk
832ea3e brief 05 phase 2: sweep, tray, upstream chain and statistical yield
b6e9c6e brief 05 phase 1: review fixes R1 to R6
d0b203f brief 05 phase 0: setup
5469737 brief 05: add brief
421fc08 brief 03: report, API, 3D explorer
```

(Phase 4's facts were committed after phase 5, as the progress log records.)

## Checks per phase

| Phase | Commit | pytest | ruff check | ruff format | web build | typecheck | e2e | Vitest |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | d0b203f | 147 passed | clean | clean | n/a | n/a | n/a | n/a |
| 1 | b6e9c6e | 149 passed | clean | clean | ok | ok | 1 passed | n/a |
| 2 | 832ea3e | 206 passed | clean | clean | ok | ok | 1 passed | n/a |
| 3 | 83416c0 | 238 passed | clean | clean | n/a | n/a | n/a | n/a |
| 4 (engine) | 3b4f339 | 301 passed | clean | clean | n/a | n/a | n/a | n/a |
| 5 | 5558b7e | 335 passed | clean | clean | n/a | n/a | n/a | n/a |
| 4 (facts) | 9e8da7d | 364 passed | clean | clean | n/a | n/a | n/a | n/a |
| 6 | 24aa45a | 382 passed | clean | clean | n/a | n/a | n/a | n/a |
| 7 | a78fb8f | 404 passed | clean | clean | ok | ok | 1 passed | n/a |
| 8 | 58b63de | 456 passed | clean | clean | ok | ok | 13 passed | 21 passed |
| 9 | d4eeeef | 472 passed | clean | clean | ok | ok | 14 passed | 21 passed |
| 10 | 7002ed4 | 480 passed | clean | clean | ok | ok | 14 passed | 21 passed |

Final run (phase 10): pytest 480 passed; coverage 98 % of src/oicd (3769 statements, 80 missed); ruff check and ruff format clean; mypy --strict clean on 40 files; every hand-calc script runs on the standard library; the 11 figures render; the generated API types match the API; tsc clean; Vitest 21 passed; Vite build ok; Playwright 14 passed (SwiftShader).

Uncovered lines (98 %): defensive branches and 422 paths in `api_physics.py`, invalid-input branches in `physics/bidi.py`, axis validation in `sweep.py`, fan-out search edges in `upstream.py`, type guards in `units.py`, rare validation messages in `twin/catalog.py`, and the `__init__` entry point (exercised through `oicd.cli.run`).

## Most interesting inferences and open tensions

- **The reference plane decides the rack** [INFERENCE on a SYNTHETIC design]: the same worst path is −1.0016 dB with the vClick's 1.5 dB in the channel, −0.0016 dB at "below 1 dB", and +1.9984 dB with the vClick on the module side of TP2/TP3.
- **Rack-scale yield returns to about 4.7σ** [INFERENCE]: y^8192 gives 0.4408 at y = 0.9999 and 0.9213 at 0.99999; a 99 % rack needs 0.99999877 per link.
- **Interleaved BiDi and ring aliasing** [INFERENCE from PEER_REVIEWED ring data]: interleaving gains 5.935 dB of isolation (−15.846 → −21.781 dB per neighbor at Q 3500), but a 1.8 THz ring puts images of seven of eight receive rings on local transmit channels, and the worst receive channel's co-directional penalty is 0.3710 dB against 0.0944 dB at 3.2 THz: the 16λ BiDi link wants FSR ≥ 3.2 THz (R ≤ 3.5501 µm at n_g 4.2).
- **"DR compatible"** [INFERENCE]: the L20's 1331 nm direction lies 13.5 nm above the draft DR wavelength range, so the phrase cannot mean draft-DR wavelength compliance in both directions.
- **Guide DR provisioning** [INFERENCE]: with the §10 chain [SYNTHETIC], 200 mW per fiber driving 4 lanes leaves +6.4398 dB unallocated; the laser supports 17 lanes per fiber. Either the real chain loses about 6 dB more or the laser is provisioned for aging, temperature and TDECQ corners; both are carried as hypotheses.
- **The 204.8 Tbps switch tray** [TENSION]: per direction (four Guide DR, the vendor's release) or aggregate (two, Counterpoint and INE); tray height 1 RU against 2 RU stays a CONFLICT between sources.
- **M1000 power density** [INFERENCE]: 1.5 kW over 7,735 mm² is 0.194 W/mm² (0.375 W/mm² over the 4,000 mm² interposer), so ">1.4 W/mm²" reads as a local or capability figure; "800 Gbps / fiber" against 448 Gb/s stays a CONFLICT.
- **Pod example** [TENSION]: HOTI26's "32 Tbps / XPU" gives 163,840 duplex fibers against "about 130,000" (26 % off), while 25.6 Tbps gives 131,072 (0.8 %); "~16,000 fewer connectors" fits two mated pairs per path with 16-fiber ferrules [SYNTHETIC].
- **Photonic processor** [INFERENCE]: the published counts multiply out (65.536 TOPS, 262.144 TOPS, 77.8 W, 349.44 and 785 mm²); only the ±n reading of the ADC range agrees with the SI's 24-bit output word; the per-cell optical power is about 9 µW whichever way the eight lasers map to the four cores; the web's "262T Ops/Watt" matches the SI's PTC-encoding-only efficiency, not the 0.81 TOPS/W system average.
- **L20 energy** [TENSION, kept]: 30 W over 6.4 Tbps is 4.6875 pJ/bit, consistent with the product page's 5 pJ/bit; the Business Wire copy's 3.0 pJ/bit would need 19.2 W.

## The model card: wrong or ambiguous points

- **§15.3, the ABFP output range.** The SI applies Q_11 with a [−1, 1] clamp to the 128-term sum as written; basumallik2022_abfp normalizes by n. The card carries both as H_out_n and H_out_1 and simulates H_out_n; the literal reading clips most sums. The sources, not the card, are ambiguous; the paper's main text (paywalled) may resolve it.
- **§15.3, the noise model** is sized by the ADC's ENOB (SYNTHETIC); the SI says the measured error tails fit a logistic better than a Gaussian.
- **§13.1, the image sum** of the periodic Lorentzian peaks 0.0047 dB above 1 at Q 3500 and FSR 1.8 THz. The card keeps the brief's model and states the approximation (D05-64).
- **§13.2, the crosstalk penalty form** −10·log10(1 − kX) is an inference; the alternative 10·log10(1 + X) is reported beside it and was not confirmed in an open source.
- **§12.4, the diplexer extension** of the reflection-crosstalk formula is an inference, and the source's derivation (NRZ, threshold adjustment) was not re-derived for PAM4.
- **§11, normal losses**: independence and normality are assumptions; real connector loss is non-negative and skewed.
- **§14.9, the PRIZM TMT loss**: the brief cites Corning's LAN-3581 sheet, which could not be opened; the 0.5 dB comes from US Conec's PRIZM TMT sheet (usconec_prizm_tmt), and the switch-tray connector's 0.5 dB is SYNTHETIC (D05-49, D05-50).
- **§4, fiber attenuation**: the 0.40 dB/km G.652.D cable maximum is applied to metre-length jumpers; G.652 itself warns against that, and the card states the difference is below 0.01 dB at rack lengths.
- **§15.2, efficiency**: 65.536 TOPS / 78 W = 0.8402 TOPS/W against the SI's 0.81 average, accepted as CONSISTENT within 5 %; the SI does not say how its average was taken.

## Not done or not measurable

- The brief's 60 fps target for the full rack on a laptop could not be measured: the e2e suite runs on SwiftShader (D05-88). The dev build shows an fps meter.
- PNG export at 2× is implemented but not covered by an e2e test.
- The photonic processor's Nature main text could not be opened (paywalled); its facts come from the SI, Table 1 and figure pages, and each catalog note says so.
## Every assumption (SYNTHETIC)

Catalog assumptions (nominal, range, rationale). Profile inputs are SYNTHETIC too and say so in their own provenance (profiles/*.json).

| assumption | nominal | range | unit | rationale |
| --- | --- | --- | --- | --- |
| `bidi16.ring_fsr_thz` | 1.8 | 1.8 to 3.2 | THz | FSR of the 16λ link's rings, not disclosed. H_fsr18: the OFC 2025 ring (1.8 THz); H_fsr32: an FSR covering the whole 3.2 THz grid (INFERENCE). |
| `bidi16.two_directions` | 2 | 2 to 2 | count | One fiber carries both directions. |
| `bidi16.return_loss_db` | 15.5 | 15.5 to 15.5 | dB | Return loss at the fiber interfaces: the draft 200GBASE-DR1 ORL tolerance (ieee3dj.orl_tolerance_dr1) used as a stand-in, as in model card §14.5. |
| `bidi16.mpi_er_db` | 6 | 6 to 6 | dB | Extinction ratio for the MPI bound (NRZ microring modulator), model card §14.5. |
| `bidi16.mpi_rt_db` | −26 | −26 to −26 | dB | Transmitter reflectance for the MPI bound, as the draft DR TX reflectance. |
| `bidi16.mpi_rr_db` | −26 | −26 to −26 | dB | Receiver reflectance for the MPI bound, as the draft DR RX reflectance. |
| `bidi16.mpi_rc_db` | −45 | −45 to −45 | dB | Connector reflectance for the MPI bound (angled connectors). |
| `guide1.fiber_power_assumed` | 100 | 100 to 110 | mW | Power per fiber between the stated 100 mW minimum and 110 mW (3.5 W / 32 fibers = 109.4 mW). |
| `guidedr.chain_loss_db` | 7.5 | 7.5 to 7.5 | dB | Non-split chain losses of model card §10: laser fiber and connector 0.5 + coupling 1.5 + excess 0 + modulator 4.0 + output coupler 1.5 dB (all SYNTHETIC). |
| `guidedr.er_db` | 4 | 4 to 4 | dB | Modulator extinction ratio of the model card §10 chain (SYNTHETIC). |
| `guidedr.reserve_db` | 0 | 0 to 0 | dB | No unallocated reserve, as in the draft DR budget of model card §12.1. |
| `guidedr.chain_extra_db` | 0 | 0 to 7 | dB | Loss in the real chain beyond the SYNTHETIC §10 chain; pinned by H_chain_lossier. |
| `guidedr.provisioning_db` | 0 | 0 to 7 | dB | Laser power held back for aging, temperature and TDECQ corners; pinned by H_laser_headroom. |
| `trays.bw_divisor` | 1 | 1 to 2 | count | Whether the tray totals are per direction (1) or aggregate of both directions (2); not disclosed. Pinned by H_dir or H_agg. |
| `trays.ine_reading` | 2 | 2 to 2 | count | ine_ocp26 calls 204.8 Tbps 'aggregate' switching bandwidth, read as both directions (INFERENCE). |
| `trays.xpu_height_ru` | 1 | 1 to 2 | RU | XPU tray height: 1 RU (PR Newswire copy, Futurum) or 2 RU (lightmatter.com copy, Counterpoint, IN Electronics). Pinned by H_xpu_1u or H_xpu_2u. |
| `l20.energy_direction_factor` | 1 | 1 to 2 | count | Directions the energy-per-bit figure divides the 30 W TDP by: 1 if per direction (as pluggables quote it), 2 if both. Not disclosed; pinned by H_l20_one_dir or H_l20_both_dirs. |
| `l20.two_directions` | 2 | 2 to 2 | count | A BiDi engine carries both directions on each fiber; used to state the both-directions rate. |
| `l20.fibers_per_lane_duplex` | 2 | 2 to 2 | count | A unidirectional DR lane uses one fiber each way, so two fibers per lane; the BiDi engine uses one. |
| `l20.lambda_tolerance_nm` | 0 | 0 to 6.5 | nm | TX wavelength tolerance δ, not disclosed: 0 as in model card §14.2, at most the half-width of the draft DR range. |
| `l200.payload_56` | 50 | 50 to 56 | Gbps | Payload carried by a 56 Gb/s lane: 50 Gb/s reproduces '32 Tbps total' (line overhead, INFERENCE), 56 Gb/s if the total counted line rate. Pinned by H_l200_payload or H_l200_line. |
| `l200.payload_112` | 100 | 100 to 112 | Gbps | Payload carried by a 106/112 Gb/s PAM4 lane: 100 Gb/s reproduces '64 Tbps total'. |
| `l200.two_directions` | 2 | 2 to 2 | count | 'Total (Tx+Rx)' counts each SerDes lane in both directions. |
| `l200.chiplets_per_package` | 4 | 1 to 4 | count | L200X chiplets per package implied by 256 Tbps / 64 Tbps (INFERENCE); not disclosed. |
| `m1000.two_directions` | 2 | 2 to 2 | count | Each SerDes has a transmitter and a receiver, so 'Tx + Rx' counts every SerDes lane twice. |
| `m1000.energy_rate_divisor` | 1 | 1 to 2 | count | Whether 2.3 pJ/bit applies to the Tx + Rx total (divisor 1) or to one direction (divisor 2); not disclosed. Pinned by H_m1000_txrx or H_m1000_per_dir. |
| `m1000.center_nm` | 1310 | 1300 to 1320 | nm | O-band operating point taken as 1310 nm, as for Lightmatter's other WDM grids; the M1000 grid is not disclosed. |
| `ptc.output_range` | 128 | 1 to 128 | count | Range of the ADC on the 128-term analog sum, in units of one product: n = 128 (basumallik2022_abfp Eq. 3) or 1 (the SI's Q_11 read literally). Pinned by H_out_n or H_out_1 (model card §15.3). |
| `ptc.path_loss_db` | 1.35 | 0.68 to 2.7 | dB | On-chip optical path from the fibre to a weight cell: 1 cm of Si ridge at the stated 1.35 dB/cm (range: 1 cm of SiN at 0.68 dB/cm to 2 cm of Si ridge). Path lengths are not disclosed (SYNTHETIC). |
| `ptc.splitter_excess_db` | 0 | 0 to 1 | dB | Excess loss of a 1:4 splitter stage that shares each laser among the four PTCs; 0 when each PTC has its own two lasers. Pinned by H_lasers_dedicated (0 dB) or H_lasers_shared (0.5 dB, SYNTHETIC). |
| `rack.switch_trays` | 8 | 8 to 8 | count | OICD-R64 design: 8 switch trays (one switch plane each). |
| `rack.xpu_trays` | 16 | 16 to 16 | count | OICD-R64 design: 16 XPU trays. |
| `rack.power_shelves` | 2 | 2 to 2 | count | OICD-R64 design: 2 ORv3 HPR power shelves (ocp_orv3_hpr72). |
| `rack.switch_tray_ou` | 1 | 1 to 1 | count | Switch tray height in OpenU: 1, as the 1RU switch tray of the release. |
| `rack.xpu_tray_ou` | 2 | 1 to 2 | count | XPU tray height in OpenU: 2 under H_2U, 1 under H_1U (the sources disagree). |
| `rack.power_shelf_ou` | 1 | 1 to 1 | count | The HPR V2 shelf is a 1 OU shelf (ocp_orv3_hpr72: 537 x 46.2 x 867.5 mm). |
| `rack.lanes_per_xpu` | 128 | 128 to 128 | count | 200G lanes per XPU each way: 25.6 Tbps per XPU, the XPU tray under H_dir. |
| `rack.switch_lanes` | 1024 | 1024 to 1024 | count | 200G lanes per switch tray each way: 204.8 Tbps under H_dir. |
| `rack.two` | 2 | 2 to 2 | count | Two fibers per duplex link, and a transmitter at each end of a link. |
| `rack.tray_fiber_m` | 0.5 | 0.5 to 0.5 | m | Fiber inside each tray on the worst path (OICD-R64 layout). |
| `rack.rack_fiber_m` | 3 | 3 to 3 | m | Rack fiber from an XPU tray to the farthest switch tray (OICD-R64 layout). |
| `rack.switch_connector_db` | 0.5 | 0.5 to 0.5 | dB | Switch-tray rear connector, TMT class (SYNTHETIC, as the PRIZM TMT figure). |
| `rack.vclick_loss_db` | 1.5 | 1 to 1.5 | dB | vClick loss: 'less than 1.5 dB' (lm_pr_vclick) taken as 1.5; Futurum's 'below 1 dB' as the low end. |
| `rack.vclicks_in_channel` | 2 | 0 to 2 | count | vClick connections counted in the TP2-TP3 channel: 2 under H_vclick_channel (model card §2), 0 under H_vclick_module. |
| `rack.reserve_db` | 0 | 0 to 0 | dB | No unallocated reserve, as in the draft DR budget. |
| `rack.zero_db` | 0 | 0 to 0 | dB | The margin a link needs (model card §3). |
| `pod.bw_per_xpu` | 25.6 | 25.6 to 32 | Tbps | Bandwidth per XPU each way: 25.6 Tbps (the XPU tray under H_dir) or 32 Tbps (HOTI26). Pinned by H_pod_256 or H_pod_32. |
| `pod.fibers_per_lane_duplex` | 2 | 2 to 2 | count | A duplex lane uses one fiber each way; a BiDi lane uses one. |
| `pod.ferrule_fibers` | 16 | 16 to 32 | count | Fibers per connector ferrule: 16, where PRIZM TMT starts (usconec_prizm_tmt: 1x16, scalable to 2x16). |
| `pod.connector_ends_per_path` | 4 | 2 to 6 | count | Connector ends a removed fiber takes out with it: 4, about two mated pairs per path (INFERENCE that reproduces about 16,000). |

## Every fact left verified = false

| fact | source | why |
| --- | --- | --- |
| `trays.nd_lane_rate` | `lightmatter_openrack_2026` | Evidence: none. Absence confirmed, not a failed lookup |
| `trays.nd_fibers_per_engine` | `lightmatter_openrack_2026` | Evidence: none. Absence confirmed |
| `trays.nd_wavelengths` | `lightmatter_openrack_2026` | Evidence: none. Absence confirmed |
| `trays.nd_power` | `lightmatter_openrack_2026` | Evidence: none. Absence confirmed |
| `trays.nd_switch_asic` | `lightmatter_openrack_2026` | Evidence: none. Absence confirmed |
| `ptc.interposer_dims` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.interposer_length_mm` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.interposer_width_mm` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.ptc_die_dims` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.ptc_die_length_mm` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.ptc_die_width_mm` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.dci_die_dims` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.dci_die_length_mm` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.dci_die_width_mm` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.ptc_power_each` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.dci_power` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.adc_enob` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.adc_rate` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.adc_power` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.vdac_enob` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.vdac_power` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.tia_gain` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.tia_bw` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.tia_noise` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.gain_design_target` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.vmod_bw` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.vmod_il` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.vmod_vpil` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.pd_bw` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.loss_si_ridge` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.loss_sin` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.vgroove_loss` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.laser_count` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.laser_power_fibre` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.laser_grid` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `ptc.laser_wallplug` | `ahmed2025_nature` | Evidence: none. Not found: the main text and Methods of ahmed2025_nature are paywalled (nature.com serves a preview only; no open-access copy via the nature.com PDF link, OpenAlex, Europe PMC/PMC, Semantic Scholar, arXiv or the Wayback Machine) |
| `prizm.insertion_loss` | `corning_tmt_lan3581` | Evidence: none. corning_tmt_lan3581 (LAN-3581-AEN.pdf) could not be opened: HTTP 403 Akamai 'Access Denied' on curl with a browser user agent (SRC/corning_tmt_lan3581_retry/raw.html), on curl with full browser headers (SRC/corning_tmt_lan3581_retry2/raw.bin),  |
| `prizm.availability` | `corning_tmt_lan3581` | Evidence: none. corning_tmt_lan3581 (LAN-3581-AEN.pdf) could not be opened: HTTP 403 Akamai 'Access Denied' on curl with a browser user agent (SRC/corning_tmt_lan3581_retry/raw.html), on curl with full browser headers (SRC/corning_tmt_lan3581_retry2/raw.bin),  |
| `prizm.fibers_per_ferrule` | `corning_tmt_lan3581` | Evidence: none. corning_tmt_lan3581 (LAN-3581-AEN.pdf) could not be opened: HTTP 403 Akamai 'Access Denied' on curl with a browser user agent (SRC/corning_tmt_lan3581_retry/raw.html), on curl with full browser headers (SRC/corning_tmt_lan3581_retry2/raw.bin),  |
| `prizm.fibers_scaled` | `corning_tmt_lan3581` | Evidence: none. corning_tmt_lan3581 (LAN-3581-AEN.pdf) could not be opened: HTTP 403 Akamai 'Access Denied' on curl with a browser user agent (SRC/corning_tmt_lan3581_retry/raw.html), on curl with full browser headers (SRC/corning_tmt_lan3581_retry2/raw.bin),  |
| `prizm.beam_diameter` | `corning_tmt_lan3581` | Evidence: none. corning_tmt_lan3581 (LAN-3581-AEN.pdf) could not be opened: HTTP 403 Akamai 'Access Denied' on curl with a browser user agent (SRC/corning_tmt_lan3581_retry/raw.html), on curl with full browser headers (SRC/corning_tmt_lan3581_retry2/raw.bin),  |
| `prizm.remates_no_cleaning` | `corning_tmt_lan3581` | Evidence: none. corning_tmt_lan3581 (LAN-3581-AEN.pdf) could not be opened: HTTP 403 Akamai 'Access Denied' on curl with a browser user agent (SRC/corning_tmt_lan3581_retry/raw.html), on curl with full browser headers (SRC/corning_tmt_lan3581_retry2/raw.bin),  |
| `prizm.blind_mate` | `corning_tmt_lan3581` | Evidence: none. corning_tmt_lan3581 (LAN-3581-AEN.pdf) could not be opened: HTTP 403 Akamai 'Access Denied' on curl with a browser user agent (SRC/corning_tmt_lan3581_retry/raw.html), on curl with full browser headers (SRC/corning_tmt_lan3581_retry2/raw.bin),  |
| `ieee3dj.revcom` | `simms2026_3dj_tt` | Evidence: none. Not in any source read; the adopted timeline (projdoc/timeline_3dj_241114.pdf) is a chart with no extractable dates |

44 facts in all are unverified.

## Every decision logged this run (docs/decisions_pending.md, D05-1 to D05-97)

| id | decision | picked |
| --- | --- | --- |
| D05-1 | Brief 05 says brief 04 is `briefs/04-refine-v2.md`; the repo holds `briefs/04-state-of-the-art-explorer.md` (untracked) and there is no `v2` branch. Where does the file go, and is any brief 04 work present? | (b): committed in "brief 05: add brief" (5469737). No brief 04 work exists (no v2 branch, no "brief 04 phase" commits), so all of brief 04 is done through brief 05. |
| D05-2 | Phase 0 commits must not touch main. | (b): `git switch -c v2` before the first commit, so main still ends at d37b15d. |
| D05-3 | The brief asks for "the commit hash" next to each ticked item, but a commit cannot contain its own hash. | (b). The final phase's hash goes into a last commit with the run summary. |
| D05-4 | How is headroom computed so that the TP3 flag always agrees with the verdict? | (b). The card (§3) states the definition as P − threshold and adds that the engine evaluates it in M_net's order, so headroom_db(TP3) equals margin_db bit for bit. |
| D05-5 | R1 says the web colors fiber and bars "from that flag only". The brief 03 fiber also shaded lightness by \ | up to 3 dB. |
| D05-6 | R5: the stable identity for a selection. input_path carries the channel index, so it changes when a connector is inserted before the RX FAU. | (b). |
| D05-7 | The R1 test values are not in the model card, but CLAUDE.md rule 6 says test expectations come from the card. | (b): T16 added with a §7 row. |
| D05-8 | "Verdict and TP3 flag always agree": the overall verdict also includes the electrical and wavelength checks, which the TP3 flag does not see. | Both are asserted, on links whose electrical and wavelength checks pass (the property's generator), where the two coincide. |
| D05-9 | README check commands used npx, which the brief forbids. | Switched to `npm run typecheck`, `npm run build`, `npm run e2e` (added the `e2e` script). |
| D05-10 | §8 "any two numeric inputs": which inputs can be swept? | (b). Electrical inputs are categorical matches (TX must equal RX), so a sweep of one side only maps the mismatch. |
| D05-11 | The web must not compute physics, but the Design space view needs the 0 dB contour. | (b): marching squares at 0 dB in `sweep.py`, returned as segments, plus best and worst cells. |
| D05-12 | Tray lane numbering: "lane 5" could be 1-based or 0-based. | (b): lane 5 is index 5 (the sixth lane). |
| D05-13 | §9 deciding lane when the excluded lane is not the lowest-margin lane (e.g. a wavelength fail with a large margin). | (b); tray margin stays the minimum lane margin; ties go to the lowest index. |
| D05-14 | Upper limit on lanes per tray request. | 1024 (the §9 text says so). |
| D05-15 | Where does the upstream chain live and how does it coexist with the fixed TP2? | (b). POST /evaluate takes either form of the same Link; the derived TP2 is labeled INFERENCE in the report's upstream section. |
| D05-16 | §10 says "OMA from P_avg and ER with the §3 formula". The §3 formula is in mW; the code uses its exact dB form, P_OMA = P_avg + 10·log10(2(ER−1)/(ER+1)). | (b); `avg_to_oma` stays for input conversion (T08). The two agree to ~1e-15 dB. |
| D05-17 | max fan-out search bounds and the "nothing fits" case. | Search N = 1 … 65536 (exponential then binary search); 0 when N = 1 is already excluded or the electrical or wavelength check fails. |
| D05-18 | §11 distribution model details. | `LossElement.loss_distribution` (mean and σ, each a Quantity with provenance). Samples are not truncated at 0 dB, so Monte Carlo matches the analytic model; Monte Carlo counts M ≥ −ε like the verdict. |
| D05-19 | /yield limits and defaults. | n_samples 1 … 10^6 (default 10^5), bins 1 … 400 (default 60, over M_mean ± 5σ with below/above counts), seed ≥ 0 (default 0). |
| D05-20 | Typed request bodies vs brief 03's manual validation. | Typed bodies (needed for the OpenAPI types of Phase 7) with handlers that keep brief 03's 422 format {"detail", "errors"} and turn UnitMismatchError into 422. |
| D05-21 | The report JSON gains an `upstream` key (null for a fixed TP2), and LossElement gains `loss_distribution`. | Additive fields only; old Link JSON still validates. |
| D05-22 | Shared test builders (chain, sigma) need importing from test modules. | `tests/__init__.py` added; tests import from `.conftest`. |
| D05-23 | The brief's §12 numbers (OMA −1 + TDECQ, budget 6.7 dB, penalties 3.7 dB) differ from welch2023_3dj_baseline (−1.2 + MAX(TECQ,TDECQ), 6.5 dB, 3.5 dB). | (b): johnson2025_3dj_mpidgd proposed them and dawe2026_3dj_er199 states them as the current draft. The card's §12.1 table cites each value to the source that states it. |
| D05-24 | Open comment R2-199 (dawe2026_3dj_er199) proposes ER 3 dB, sensitivity −4.5 + TECQ, budget 6.9 dB, penalties 3.9 dB. Its outcome is in no source read. | (b). |
| D05-25 | Appendix A8 says OMAouter min "−1 + max(TECQ, TDECQ)" "for ER ≥ 3.5 dB". No source read says "for ER ≥ 3.5 dB". | Dropped from the card; ER min 3.5 dB is stated as its own row. The Phase 4 catalog keeps the Appendix wording with verified = false for that qualifier. |
| D05-26 | Appendix A8 "RevCom planned December 2026" is in none of the four 802.3dj sources; the adopted timeline (projdoc/timeline_3dj_241114.pdf, opened) is a chart with no extractable dates. | Unverified (verified = false in Phase 4); not used in any computation. |
| D05-27 | "RX sensitivity reference −4.3 dBm (ideal transmitter)": the draft caps the receiver requirement at −3.4 dBm for TECQ < 0.9 dB, so −4.3 dBm is the intercept of the −4.3 + TECQ line. | (b), stated in §12.1 and in the profile rationale. |
| D05-28 | Class of the profile's TX OMA 2.4 dBm (= −1 + 3.4). | PROPOSED_STANDARD, rationale shows the formula and its limit. |
| D05-29 | Source class of bhatt2016_mpi, anslow2017_drrefl and bhatt2001_bidixtalk (task-force and study-group contributions, not standards). | PROPOSED_STANDARD, noted in each bib entry. |
| D05-30 | Table 180-12 lookups outside the table (more than 6 or 8 reflectances). | Not supported (None); negative or non-integer counts raise. |
| D05-31 | The DR profile's wavelength: the draft gives a range, the schema a centre and tolerance. | TX 1311 ± 6.5 nm into RX 1304.5 to 1317.5 nm; both clearances 0. |
| D05-32 | §14.1: when is a failed check TENSION and when CONFLICT? The brief's examples call derived-versus-claim gaps TENSION (L20 3.0 pJ/bit, HOTI26 32 Tbps/XPU) and source-versus-source gaps CONFLICT (M1000 800 vs 448 Gb/s, NRZ | (b): CONFLICT when both sides are facts, TENSION when a derived node or assumption is involved. Each outcome also reports whether the intervals, widened by the tolerance, overlap. |
| D05-33 | Intervals of facts: "approx" and "min"/"max" facts have no stated width. | (b). A fact is a point unless the source gives a range (nominal = middle of the range). "min"/"max" act through `bound` checks. |
| D05-34 | The brief's TOML field lists are minimal. | Added optional `location` and `note` to facts (a note is required when verified = false), `kind` (product, reference or system) to [product], `group` and `note` to hypotheses, and part fields (assembly, shape, position,  |
| D05-35 | What may a hypothesis set? | Assumptions only, inside their [low, high]; at most one hypothesis per group is applied; hypotheses override user overrides. |
| D05-36 | "Corner evaluation over parent intervals": immediate parents or interval ancestors? | Transitive interval ancestors (each corner re-evaluates the whole subgraph), Monte Carlo above 12 of them (4096 uniform samples, seed 20261018, flagged). |
| D05-37 | Non-numeric facts (modulation, foundry, "edgeless I/O"). | Kept with `unit = "text"` and no value; they can be conflicts but cannot feed formulas. |
| D05-38 | Card section order: §13 belongs to phase 5 but §14.1 had to precede the phase 4 engine. | §13 holds a one-line placeholder until phase 5. |
| D05-39 | lm_ofc25_talk gives "Q 3500" without saying loaded or intrinsic (finding of the G4 fact check). | Loaded (Q_L): the brief's FWHM 65.3855 GHz = f0/3500 implies it, and a linewidth measurement gives the loaded Q. Recorded as an assumption in the twin. |
| D05-40 | 16λ BiDi worst receive channel: the brief names channel 3 (H_fsr18) and 7 (H_fsr32), but channels 3 and 13 tie on X, and under H_fsr32 (FSR = the whole 16-channel span) all eight rings are physically identical. | (b): largest X-crosstalk + reflection penalty; totals within 1e-6 dB tie; ties go to the channel nearest the grid centre, then the lower index (§13.6). Channel 3 wins on reflected X_r (0.6438 vs 0.6436 dB); under H_fsr32 |
| D05-41 | BiDi model reference planes. | TP2 = TX engine output before its diplexer, TP3 = RX engine input after its diplexer, so both diplexers are loss elements ("diplexer IL at both ends"); the reflection crosstalk uses the TP2-to-TP3 fiber-plus-connector IL |
| D05-42 | Thermal tuning details the brief leaves open. | Heaters only red-shift; "required" is the sum of the worst-case laser, fabrication and drift offsets; the worst-case range is one co-directional spacing with barrel shifting and one FSR without; drift dλ/dT = λ·(dn/dT)/n |
| D05-43 | Ring-weighted reflection crosstalk: R·X_r with X_r up to 1.08 (an image on a local transmitter). | Inline 10·log10(T/(T − R·X_r)); X_r > 1 would be a negative isolation, which the §12.4 function rightly rejects. |
| D05-44 | ITU-T G.652 says its 0.40 dB/km should not be applied to short jumper or indoor cables (1.0 dB/km or less cited for indoor cable). | Keep 0.4 dB/km as the brief says, and state the caveat in §4 and §13.7; at rack lengths the difference is below 0.01 dB. |
| D05-45 | "Verify 10·log10(1 + X) in Agrawal or another open source." | Agrawal was not opened; andre2000_xtalk (eq. 8, NRZ heterodyne crosstalk with adjusted threshold) was, and is cited. |
| D05-46 | bogaerts2012_mrr: Wiley returned 403. | Abstract from the TU/e research portal, cited only as a review, never for a number. |
| D05-47 | Rule 1 for physics endpoints whose inputs are plain numbers. | The BiDi model accepts a bare number as a SYNTHETIC what-if input or {value, provenance}; computed penalties and the fiber loss are INFERENCE with the formula and inputs in the rationale. |
| D05-48 | How to verify about 300 Appendix A facts against about 60 sources. | Seven agents, one per source group, each writing exact quotes with their evidence type; the coordinator then re-checked every "text" quote by program against the downloaded source text (Unicode NFKC and collapsed whitesp |
| D05-49 | A source that could not be opened still has to appear as the `cite` of the unverified facts that keep its Appendix wording, but rule 14 forbids a references.bib entry for it. | (b): `catalog/unopened_sources.toml` records the key, URL, everything tried and the result; only unverified facts may cite it (or `appendix_a` when no source is named). Verified facts must cite references.bib. |
| D05-50 | Corning's LAN-3581 datasheet (PRIZM TMT) never opened (HTTP 403 everywhere, no archive copy). The rack's 0.5 dB blind-mate loss cites it in the brief. | (b), key `usconec_prizm_tmt` (PUBLISHED_SPEC). The sheet does not say maximum or typical; the rack uses 0.5 dB as the worst-case element loss and says so. The 80 µm beam, 50 re-mates and Q4 2026 availability stay unverif |
| D05-51 | Sources found by the fact check that are not in Appendix B. | Added after opening: lm_pr_openrack (lightmatter.com copy of the Open Rack release), counterpoint_nvlinkfusion (the actual source of "128 lasers per chip"), usconec_prizm_tmt, lm_web_ptc, lm_web_about, lm_blog_newcompute |
| D05-52 | Source classes the brief leaves open. | HOTI 2025 paper: PEER_REVIEWED by venue (the paper does not state its review). OCP open silicon photonics vision: PROPOSED_STANDARD (non-normative; first author from Lightmatter). Converge Digest and DatacenterDynamics:  |
| D05-53 | The Nature paper's main text and Methods are paywalled; the free Supplementary Information, Table 1 page and figure pages were read. | 25 A9 values found only in the main text stay unverified with the Appendix wording (die sizes, PTC 3.2 W, control dies 65 W, ADC/DAC/TIA figures, gain target 4, modulator, PD, waveguide, V-groove and laser figures). Sub- |
| D05-54 | The web's "262 trillion operations per watt": the SI itself gives 262 TOPS/W counting only the PTC encoding energy (0.25 W), while the paper's headline 262 is per second at 2 GHz. | Both: the CONFLICT with the paper's per-second figure stays, and phase 9 carries two hypotheses (a per-second figure mislabeled, or the SI's encoding-only efficiency) with the support matrix showing which claim each matc |
| D05-55 | "Not disclosed" items (lane rate, fibers per engine, wavelengths, power, switch ASIC of the OCP trays). | Recorded as unverified text facts whose note says the absence was confirmed in all five tray sources. |
| D05-56 | Product summaries in the catalog. | Without numbers: every number lives in a fact, an assumption or a derived node and is badged with its class. |
| D05-57 | Where do the ring, fan-out, pod and rack computations live relative to the inference graph? | (b), as the brief's "plus a physics evaluation where one applies"; the Guide DR fan-out is in both (graph formula `chain_margin_db` and the engine's upstream chain), and they agree to 4 decimals. |
| D05-58 | Two checks in the brief compare derived nodes with each other (grid span against ring FSR, OU used against frame capacity), which the "bound" kind could not express. | Optional `relation` (le, ge) on bound checks, added to §14.1 first. |
| D05-59 | POST /ptc/simulate is listed in phase 7, but the processor model (`oicd.compute.ptc`) is phase 9. | Added in phase 9 together with the model it serves. |
| D05-60 | openapi-typescript 7.13.0 (the latest) declares a TypeScript ^5 peer; the explorer is on TypeScript 6.0. | `--legacy-peer-deps`; the generated `web/src/api/schema.ts` typechecks under TS 6. |
| D05-61 | Keeping the generated types fresh. | `scripts/dump_openapi.py` writes `web/openapi.json` (sorted keys); `npm run gen:api` regenerates `schema.ts`; a pytest fails when `web/openapi.json` no longer matches the API; CI (phase 10) reruns gen:api and checks for  |
| D05-62 | POST /inference overrides outside an assumption's [low, high]. | Accept any finite value as a what-if (pinned_by "override"); hypotheses must stay inside the range. |
| D05-63 | Ring spectra for the Spectrum tab. | The API samples drop responses (/ring, /wdm/crosstalk) in linear and dB. |
| D05-64 | The image sum of §13.1 peaks above 1 (+0.0047 dB at Q 3500, FSR 1.8 THz). | Kept, stated in §13.1 with a hand-calc line. |
| D05-65 | False color for O-band wavelength channels (phase 8). | Hue by direction (blue = direction A on even n, orange = direction B on odd n), lightness by channel position as a weak secondary cue; channel identity always by label. |
| D05-66 | Where explorer colors and materials come from. | GET /display (`src/oicd/display.py`): class and dims-class swatches, reserved status colors with icons, the diverging margin map (±3 dB, gray at 0 dB), channel colors, surfaces and PBR materials; neutral reference palett |
| D05-67 | A part whose axes have different provenance (L20 substrate: VENDOR footprint, SCHEMATIC thickness). | Optional `dims_axes` (x, y, z) per part; `dims_class` must equal the weakest axis; the Inspector badges each axis. |
| D05-68 | Guide DR LNIC size: the release says "built to OCP NIC 3.0 dimensions" without SFF or LFF. | Drawn as SFF; width class INFERENCE (our reading), depth PUBLISHED (115 mm in both sizes), thickness SCHEMATIC; the Inspector lists both widths. |
| D05-69 | Units of the zoom levels "Rack (m) → Tray (cm) → Engine (mm) → PIC (µm) → Ring (nm)". | Rack, trays and packages are stored in mm (their facts are in mm; float32 is ample at 2.3 m); the PIC region is a µm scene and the ring cross-section an nm scene. The scale bar and the measure tool pick m, cm, mm, µm or  |
| D05-70 | Scene coordinate convention. | TOML: x width, y depth (front at −y), z up; positions are centers. The web maps (x, y, z) → three.js (x, z, −y). |
| D05-71 | PIC region and ring cross-section content: the L20's PIC layout and modulator type are not disclosed. | A representative microring BiDi lane (OFC 2025 ring paper: MRM, MRR, Ge PD, heater; Hot Chips 2025: ~15 µm, resistive heater, depletion PN junction); ring diameter INFERENCE (cross-source), all else SCHEMATIC; the scene  |
| D05-72 | Tour captions. | Each stop names a catalog node or check; the engine writes the caption (value, derivation, source) and its badge (class or check status). Written notes remain possible (badge "note") but no shipped stop uses one. |
| D05-73 | Pulse brightness "follows the API's linear power". | Trace points carry `power_mw` (model card §3, §7 row). |
| D05-74 | Where the physics overlays (light paths, pulses, margins, heaters) are computed. | GET /overlay/{scene} (`src/oicd/twin/overlay.py`): paths with samples (position, power in mW, brightness), part values with margin colors or heater power, cases (the rack's reference planes), notes. The trace is spread e |
| D05-75 | Margin colormap bins. | 0.4 dB bins, saturating beyond ±2.8 dB, with a neutral bin of ±ε (the verdict's 1e-9 dB), served as `margin_bins`; overlays carry the color itself. |
| D05-76 | Pulse brightness and the BiDi ghost. | Linear in power relative to the scene's reference (the brief's wording). At the §13.8 case's 25 dB diplexer isolation the ghost is 37.8 dB below the signal and invisible; the BiDi link scene has an isolation control (0 t |
| D05-77 | Light whose power is not public (M1000, L200 fibers, laser supply of the L20, the representative PIC lane). | Drawn steady at a fixed display brightness with no pulses and power_mw None, labelled "power not disclosed". |
| D05-78 | Which transmitter's power sets a BiDi direction's crosstalk power. | The local transmitter's OMA (model card §13.7); the §12.4 penalty keeps the source's equal-power form. |
| D05-79 | Inputs of the Upstream and Yield views. | `profiles/upstream_example.json` (§10 chain on the worked example, N = 16) and `profiles/yield_example.json` (§11: the three matings at σ 0.2 dB), all SYNTHETIC; the views edit them as what-ifs (relabelled SYNTHETIC). |
| D05-80 | Spectrum tab inputs. | GET /spectrum/bidi16?hypothesis=H_fsr18 or H_fsr32: grid, ±20 GHz accuracy and receive-ring responses, every input a catalog node. |
| D05-81 | Citations with source links. | GET /references parses references.bib (title, year, url, note); the Inspector links each cite to its url. |
| D05-82 | "Thin emissive tubes" for light paths. | Pixel-width lines (three Line2) per channel, pulses as pixel-size points; brightness from the API, HDR emission so only light paths bloom (luminance threshold 1, the selective-bloom mechanism). |
| D05-83 | Light inside opaque carriers (fibers, bundles, waveguides). | With overlays on, parts that carry a light path render at 32 % opacity. |
| D05-84 | Fit all / fit selection. | camera-controls fitToSphere with a 12 % margin. |
| D05-85 | Leader labels. | A probe in the canvas projects anchors on camera change; one DOM layer draws the labels with a greedy declutter (longer leaders, then hidden unless selected). |
| D05-86 | Section caps. | Stencil caps (back faces +1, front faces −1) under one 45° hatch in the palette's muted ink; transparent parts are cut without caps. |
| D05-87 | Undo and redo scope. | Design edits: the link, the tray lanes and lane edits, the loaded example profiles. View state (camera, selection, section, explode) is URL state instead. |
| D05-88 | Playwright rendering. | SwiftShader software GL (as brief 03); a frame can take seconds, so tests wait on the viewport's data-settled flag (no camera change for 0.7 s). The 60 fps rack target cannot be measured in CI; the dev build shows an fps |
| D05-89 | Measure-tool test. | `window.__oicd.corner(part, signs)` returns a part's bounding-box corner on screen; the test clicks near two corners, the tool snaps to the feature-edge vertices and reads 37.5 mm for the L20 outline. |
| D05-90 | The brief 03 web code. | Replaced: its behaviors (worked example, sliders, waterfall, checks, provenance with threshold terms, R1 flag coloring, R5 stable keys, connector insert) live in the Link budget tab and the schematic link scene; the smok |
| D05-91 | Two readings of the ABFP output quantizer: the SI's Q_11 with a [−1, 1] clamp on the 128-term sum, or basumallik2022_abfp's range ±n. | Both as hypotheses H_out_n and H_out_1 (catalog assumption ptc.output_range, check against the SI's 24-bit output word); simulations default to H_out_n, the API takes either. |
| D05-92 | ADC noise model. | Additive Gaussian on the analog sum (the SI's model), σ from SNR = 6.02·ENOB + 1.76 dB over the ADC range (SYNTHETIC sizing); the SI's note that the tails fit a logistic better is stated in §15.3. |
| D05-93 | bfloat16 scale rounding. | Up to the next bfloat16 value (the brief's hand case), so no normalized value exceeds 1. |
| D05-94 | MLP experiment dataset and gains. | 10-class Gaussian mixture in 128 dimensions (spread 0.35, seed 0), 128-128-128-10 ReLU MLP trained in float64 with Adam; gains 0.1 to 8 so that the low-gain collapse is visible; reported as INFERENCE on synthetic data, n |
| D05-95 | Dimension class of the paper's die and interposer sizes. | PUBLISHED for the footprints given in the peer-reviewed paper (catalog class peer_reviewed), SCHEMATIC thicknesses and arrangement; the 2 × 2 placement under two control dies is inferred from the footprints and stated in |
| D05-96 | Per-weight-cell optical power: the laser-to-core mapping is not disclosed. | H_lasers_dedicated (two lasers per core) and H_lasers_shared (each laser split four ways, SYNTHETIC 0.5 dB excess) with a SYNTHETIC 1 cm on-chip path; 9.70 and 8.64 µW per cell. |
| D05-97 | e2e check of the simulator. | The test asserts that the error at G = 4 is below the error at G = 1 (model card §15.4) rather than copying numbers from a run. |
