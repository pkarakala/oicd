# Model card: optical link feasibility (Milestone 1)

Author: Pranav. This card is the spec: code implements it, tests take their expected values from it. All component values are **synthetic** unless a citation key is given.

## 1. Scope

The model decides whether a single point-to-point optical lane is **not excluded** by three constraints: electrical interface match, wavelength containment, and worst-case optical power budget.
It does not decide BER, eye quality (TDECQ), dispersion, reflections and multipath interference, thermal behavior, or reliability. These are always reported as `NOT_EVALUATED`.

## 2. Reference planes

```
laser out ──► [laser fiber + connector] ──► PIC in ──► [split 1:N] ──► [modulator] ──► [out coupler] ──► TP2
TP2 ══► [TX FAU mating] ══► [fiber] ══► [patch connector] ══► [fiber] ══► [RX FAU mating] ══► TP3 ──► [RX coupler] ──► PD
```

- **TP2:** the transmitter's optical output at its fiber interface, before the first mated connection. Transmitter OMA is specified here, so everything upstream (laser, split, modulator, coupler) is inside the transmitter spec.
- **TP3:** the receiver's optical input at its fiber interface, after the last mated connection. Receiver sensitivity is specified here, so the receiver's own coupler and photodiode response are inside the receiver spec.
- **Inside the Milestone 1 budget (TP2 to TP3):** the passive channel only: every mated connector or fiber-array-unit (FAU) interface, fiber attenuation, and any shuffle or patch panel. This is the channel insertion loss.
- **Upstream, deferred to Milestone 2:** laser power, laser-to-PIC coupling, split loss 10·log10(N), modulator insertion loss, output coupler. Milestone 2 derives TP2 from these instead of taking it as an input.

This convention follows the TP2/TP3 split used by IEEE 802.3 optical PMD clauses (to be cited once the clause is read).

## 3. Equations

Power budget, worst case, OMA throughout:

```
P_TP3,OMA [dBm] = P_TP2,OMA,min [dBm] − Σ L_i,max [dB]
M_net [dB]      = (P_TP3,OMA − S_RX,OMA,max) − Σ Π_j − R
PASS  iff  M_net ≥ −ε,   ε = 1e-9 dB
```

Threshold and headroom (display quantities; M_net alone decides the verdict):

```
threshold_dbm          = S_RX,OMA,max + Σ Π_j + R
headroom_db(plane)     = P_plane,OMA − threshold_dbm
above_threshold(plane) iff headroom_db(plane) ≥ −ε
```

M_net decides the verdict. At TP3, headroom_db(TP3) = P_TP3,OMA − threshold_dbm = M_net. The engine evaluates every headroom in the order of M_net, (P_plane,OMA − S_RX,OMA,max) − Σ Π_j − R, so headroom_db(TP3) equals M_net bit for bit and above_threshold(TP3) always agrees with the power-budget verdict. Why: a display that compares headroom with 0 on its own can contradict the verdict at an exact boundary, where float sums land a few ulps below zero (T04, T16).

Each trace point also carries power_mw = 10^(P_plane,OMA/10), the same OMA in mW, and relative_power = power_mw(plane) / power_mw(TP2), the fraction of the launched OMA left, for displays whose brightness follows linear power (the explorer's pulses). Why: the web never converts units itself. Hand case (`docs/hand_calcs/s04_s05_budget.py`): in the worked example TP2 at 0 dBm OMA is 1.0 mW and TP3 at −4.0008 dBm OMA is 0.398034 mW, so relative_power(TP3) = 0.398034.

OMA from average power (only to convert inputs, never mixed in the budget):

```
OMA = 2 · P_avg · (ER − 1) / (ER + 1),   P_avg and OMA in mW, ER linear
```

Wavelength compatibility (interval containment):

```
[λ_TX − δ_TX, λ_TX + δ_TX] ⊆ [λ_RX,min, λ_RX,max]
lower clearance = (λ_TX − δ_TX) − λ_RX,min
upper clearance = λ_RX,max − (λ_TX + δ_TX)
PASS iff lower clearance ≥ −ε_nm and upper clearance ≥ −ε_nm,   ε_nm = 1e-9 nm
Δλ ≈ λ² Δf / c,   c = 299 792 458 m/s (exact, SI definition)
```

Electrical compatibility: TX and RX must match on (modulation, symbol_rate_gbd, lanes, fec). Line rate = symbol rate × bits per symbol (PAM4: 2).

Why each choice:
- **OMA, not average power:** 200G/lane DR optics specify transmitter power and receiver sensitivity as OMA, because the receiver decides between levels, so only the separation between them matters. Mixing an average launch with an OMA sensitivity overstates margin by 10·log10((ER+1)/(2(ER−1))); at ER = 4 dB that is 0.65 dB.
- **Worst case, not typical:** feasibility has to hold for every unit that ships, so the decision uses minimum launch, maximum loss and maximum (least sensitive) sensitivity. Typical values may be reported but never decide PASS or FAIL.
- **Penalties Π_j separate from reserve R:** penalties are named physical impairments (TDECQ, reflections, crosstalk, temperature, aging) that differ between architectures. R is unallocated engineering margin. Keeping them separate means a BiDi link pays its own crosstalk penalty instead of hiding it inside a shared reserve.

## 4. Worked example (by hand)

Inputs (all synthetic): P_TP2 = 0 dBm OMA. Channel, in the §2 order: TX FAU mating 1.5 dB + 1 m of single-mode fiber 0.0004 dB + patch connector 1.0 dB + 1 m of single-mode fiber 0.0004 dB + RX FAU mating 1.5 dB. The two fiber segments are 2 m at 0.4 dB/km (2 × 0.0004 = 0.0008 dB). S_RX = −6 dBm OMA, Π = 0, R = 1.5 dB.

Wavelength and electrical (synthetic): TX 1310 ± 2 nm, RX passband 1300 to 1320 nm, PAM4, 106.25 GBd, 1 lane, RS(544,514).

```
Σ L      = 1.5 + 0.0004 + 1.0 + 0.0004 + 1.5 = 4.0008 dB
P_TP3    = 0 − 4.0008                     = −4.0008 dBm OMA
M_net    = (−4.0008 − (−6)) − 0 − 1.5     = +0.4992 dB
Verdict  = PASS
```

What this shows: the 2 m of fiber contributes 0.0008 dB, 0.02% of the budget. At rack scale, connector count, not fiber length, sets the budget. The 0.4 dB/km figure is the ITU-T G.652.D maximum cable attenuation from 1310 to 1625 nm (itut_g652_2024, Table 2). G.652 says its values should not be applied to short jumper, indoor or drop cables; even at the 1.0 dB/km it cites for indoor cable, 2 m would add 0.002 dB.

## 5. Test cases

Unless stated, inputs are T01's: P_TP2 = 0 dBm OMA, S_RX = −6 dBm OMA, Π = 0, R = 1.5 dB.

| ID | What it tests | Key inputs | Expected |
| --- | --- | --- | --- |
| T01 | Nominal pass | loss 4.0 dB | M = +0.5 dB, PASS |
| T02 | Nominal fail | loss 5.0 dB | M = −0.5 dB, FAIL |
| T03 | Exact boundary | loss 4.5 dB | M = 0.0 dB, PASS (≥ −ε) |
| T04 | Boundary with non-representable floats | losses 0.3 + 1.3 + 3.3 dB, R = 1.1 dB | exact M = 0; float M = −4.44e-16; PASS only because of ε |
| T05 | Loss monotonicity | T01 plus one 0.5 dB connector | M drops by exactly 0.5 to 0.0 dB, PASS; property: adding any loss ≥ 0 never raises M |
| T06 | Named penalty | T01 with Π = 1.0 dB | M = −0.5 dB, FAIL; report and check evidence name the penalty |
| T07 | OMA/average mixing | TX AVERAGE, RX OMA | raises UnitMismatchError at schema construction (bad input, not a feasibility verdict) |
| T08 | Average to OMA | P_avg = 0 dBm, ER = 4 dB | OMA = −0.650 dBm (−0.64991) |
| T09 | Wavelength inside passband | TX 1310 ± 2 nm, RX 1300 to 1320 nm | PASS; 8 nm clearance each side |
| T10 | Wavelength edge outside | TX 1318 ± 3 nm, RX 1300 to 1320 nm | FAIL; upper edge 1321 nm exceeds 1320 nm by 1 nm |
| T11 | Electrical mismatch | TX 106.25 GBd PAM4, RX 53.125 GBd PAM4 | FAIL on symbol_rate_gbd; modulation, lanes, FEC still reported |
| T12 | Invalid physics | negative loss, 0 nm wavelength, passband min ≥ max, NaN/inf, ER ≤ 0 dB | negative loss, 0 nm wavelength, passband min ≥ max, NaN/inf rejected at schema with ValueError; ER ≤ 0 dB rejected by avg_to_oma |
| T13 | Provenance | worked example | every input in the report lists its SourceClass (all SYNTHETIC here) |
| T14 | Determinism | run T01 twice | identical reports, field for field |
| T15 | Not-evaluated list | any link | lists BER, TDECQ, dispersion, reflections/MPI, thermal, reliability |
| T16 | Trace flag at an exact boundary | losses 0.1 + 0 + 1.0 + 0 + 0.2 dB, R = 4.7 dB | exact M = 0; NOT_EXCLUDED; above_threshold(TP3) true; headroom_db(TP3) within 1e-9 of 0 and equal to M_net; property: above_threshold(TP3) agrees with the verdict for every valid link |

T04 note: the float result depends on summation order. The test asserts PASS and |M| < 1e-9; it does not assert the exact float.

## 6. What would validate this model on real hardware

- **Channel loss (TP2 to TP3):** insertion loss with a stabilized 1310 nm source and optical power meter, referenced through a launch cord, measured per mated connection and end to end. Validates Σ L.
- **TP2 OMA:** sampling oscilloscope with an optical reference receiver on a square-wave or PRBS pattern, reading P1 and P0. Validates P_TP2 and the average-to-OMA conversion via measured ER.
- **Sensitivity:** BER versus received OMA, swept with a variable optical attenuator, at the target pre-FEC BER of the link's FEC. Gives S_RX for the specific receiver. Cite the FEC threshold before using a number.

## 7. Decision log

| Date | Decision | Why | Alternative rejected |
| --- | --- | --- | --- |
| 2026-10-18 | Budget in OMA | 200G/lane DR optics specify TX and RX in OMA | Average power: simpler but mixes quantities |
| 2026-10-18 | Allow DB − DB and −DB | The margin equation subtracts penalties and reserve (both dB) from a dB difference; a gain is a negative loss | Forbid them: the margin equation could not be written |
| 2026-10-18 | Treat c as exact, no bib entry | c = 299 792 458 m/s by SI definition (2019 SI); cite the SI Brochure once read | Leave uncited: violates rule 1 |
| 2026-10-18 | Pass rule M ≥ −1e-9 dB | Floating-point sums of dB values can land a hair below zero at an exact boundary (T04) | Exact M ≥ 0: fails real boundaries at random |
| 2026-10-18 | Unit-kind mismatch raises instead of FAIL | a mismatch is invalid input, not a verdict; rule 5 applies to valid links | return FAIL: hides input bugs as physics |
| 2026-10-18 | Wavelength pass rule clearance ≥ −1e-9 nm | float edge test found −2.27e-13 nm on an edge that is exact on paper | exact containment: random failures at real edges |
| 2026-10-18 | §3 defines threshold_dbm = S_RX + ΣΠ + R, headroom_db(plane) and above_threshold(plane) with the verdict's ε; M_net decides and headroom at TP3 equals M_net (review R1, R6) | the explorer compared headroom with 0 itself and turned the RX side red under a NOT_EXCLUDED verdict at an exact boundary | let displays compare headroom with 0: two pass rules that disagree by ulps |
| 2026-10-18 | §3 defines lower and upper clearance | "both clearances" was undefined (brief 03 decision 2) | leave the definition to the code |
| 2026-10-18 | §4 lists the fiber as the two §2 segments, 2 × 0.0004 dB | matches the §2 diagram, the shipped profile and the 3D scene; Σ L stays 4.0008 dB (brief 03 decision 3) | one lumped 2 m element |
| 2026-10-18 | T16 added: trace flag at an exact boundary | review R1 found the disagreement on this input | property test only |
| 2026-10-18 | ≥, ≤ and − throughout the card instead of their ASCII spellings | one notation for every pass rule | mixed ASCII and math notation |
| 2026-10-18 | §8 design-space sweep: a 2D grid of any two power or wavelength inputs, at most 201 × 201, with the 0 dB contour | brief 05 phase 2a; shows the trade-offs a single margin hides | 1D sweeps only (brief 04 phase B) |
| 2026-10-18 | §9 multi-lane tray: excluded if any lane is, margin = minimum lane margin, deciding lane reported | brief 05 phase 2b; a tray ships as a unit | average lane margin: hides the lane that fails |
| 2026-10-18 | §10 upstream chain derives TP2 from the laser (Milestone 2), with max fan-out by search | brief 05 phase 2c; TP2 in CPO is set by the shared external laser | keep TP2 a free input: hides the split limit |
| 2026-10-18 | §11 statistical yield Φ(M_mean/σ_total) with a seeded Monte Carlo, never changing the worst-case verdict | brief 05 phase 2d; worst case over-provisions stacked connectors | replace the worst-case verdict with yield: assumption-dependent |
| 2026-10-18 | §12 draft IEEE 802.3dj 200GBASE-DR1 budget as a validation profile, M_net = 0 on paper | brief 05 phase 3; an external budget the engine must close exactly | validate only against hand cases we wrote ourselves |
| 2026-10-18 | §12.1 uses the D3.x values, not the 2023 baseline (budget 6.5, OMA −1.2 + TDECQ) or open comment R2-199 (budget 6.9) | johnson2025_3dj_mpidgd and dawe2026_3dj_er199 state the D3.x values; R2-199's outcome is unknown | the baseline: superseded |
| 2026-10-18 | §12.3 MPI as the bhatt2016 worst-case bound, stated as conservative versus the 1e-6 allocation | a closed form the engine can evaluate | a Monte Carlo of phases: not reproducible from the sources read |
| 2026-10-18 | §12.4 reflection crosstalk from bhatt2001, with a diplexer-isolation extension labeled INFERENCE | BiDi needs a reflection penalty; the extension is ours | apply the single-wavelength formula unchanged to two-wavelength BiDi |
| 2026-10-18 | Source classes PEER_REVIEWED and THIRD_PARTY added; both need a citation key | the twin cites peer-reviewed papers (some vendor-authored) and analysts, which are neither vendor claims nor specifications | fold them into VENDOR_CLAIM: hides independent and reviewed sources |
| 2026-10-18 | §14.1 twin method: facts, assumptions, derived nodes with corner intervals, CONSISTENT/TENSION/CONFLICT checks, hypotheses, support matrix, tornado | brief 05 phase 4; written before the engine, the products follow in phase 6 | one confidence score per number: hides why a number is uncertain |
| 2026-10-18 | §14.1 status rule: CONFLICT only when two facts disagree, TENSION when a derived node does | a derived node carries our reading, a fact pair is a disagreement between sources | one threshold on the gap size: mixes source disagreement with our assumptions |
| 2026-10-18 | §14.1 `bound` checks may state `relation` (le, ge) against a node that is not a min or max fact | phase 6 needs requirements between derived nodes (grid span against FSR, OU used against frame capacity) | encode each requirement as a fake min or max fact: a fact must come from a source |
| 2026-10-18 | §13.1 states that the image sum peaks 0.0047 dB above 1 (Q_L 3500, FSR 1.8 THz) | found when the API sampled the ring response; the brief's model is kept and its approximation stated | renormalize the sum to peak at 1: changes the brief's leakage values |
| 2026-10-18 | §4 fiber note cites ITU-T G.652.D (0.40 dB/km, 1310 to 1625 nm) with its short-cable caveat | brief 05 phase 5; the source was opened | keep "typical value, to be cited" |
| 2026-10-18 | §13 microring and WDM physics: periodic Lorentzian (k = −50 … 50), FWHM = f0/Q_L with the factor-2 lifetime caveat, crosstalk −10·log10(1 − kX) (INFERENCE) with 10·log10(1 + X) alongside, SYNTHETIC design window, thermal tuning with barrel shifting, interleaved Guide grid (INFERENCE), aliasing and the worst-channel rule, BiDi link model | brief 05 phase 5 | single-neighbor Lorentzian without images: misses the FSR aliasing that decides the 16λ BiDi result |
| 2026-10-18 | §3 trace points carry power_mw = 10^(P_plane,OMA/10) and relative_power | brief 05 phase 8: pulse brightness follows the API's linear power | convert dBm to mW in the browser: the web would compute physics |
| 2026-10-18 | §13.7 BiDi directions report the crosstalk power at the receiver, 10^(P_TX,local/10)·R | brief 05 phase 8: the ghost pulse's brightness is the API's crosstalk power | let the web scale the ghost from the penalty: the web would compute physics |
| 2026-10-18 | §14.2 to §14.10 product twins, the 16λ BiDi ring-FSR hypotheses, the Guide DR fan-out, tray and pod hypotheses and the reference rack OICD-R64 with its reference-plane hypotheses | brief 05 phase 6, written before the catalog graphs | per-product prose without derivations: nothing a test could check |

## 8. Design-space sweep

The margin and verdict over a 2D grid of two numeric inputs, every other input fixed.

```
M_net[j, i]   = M_net(link with x ← x_i and y ← y_j),   i = 0 … n_x − 1,  j = 0 … n_y − 1
verdict[j, i] = verdict of the same edited link (all three checks of §3)
```

- **Sweepable inputs:** `channel[i].loss_max`, `penalties[i].value` and `reserve` (dB); `tx.launch_oma_min` and `rx.sensitivity_oma_max` (dBm OMA); `tx.center_wavelength_nm`, `tx.wavelength_tolerance_nm`, `rx.passband_min_nm` and `rx.passband_max_nm` (nm). Electrical inputs are matched, not swept.
- **Axes:** 1 to 201 strictly increasing finite values each, every value valid for its input under the T12 rules, and x and y different inputs. A grid larger than 201 × 201 is invalid input.
- **Exactness:** every cell is evaluated with the §3 expressions in the §3 summation order, so a cell equals the margin of the edited link evaluated on its own, bit for bit.
- **Slopes:** M_net is affine in every power input: ∂M/∂L_i = −1, ∂M/∂Π_j = −1, ∂M/∂R = −1, ∂M/∂P_TP2 = +1, ∂M/∂S_RX = −1 (dB per dB).
- **0 dB contour:** the segments where M_net crosses 0, by linear interpolation along the grid edges (marching squares). For an affine field this is exact.
- **Best and worst cells:** the cells with the largest and smallest margin; ties go to the lowest (j, i).

Why: one margin number hides which inputs the design is close to the boundary in. The grid shows which inputs trade against each other at 1 dB per dB and where the design falls off.

Hand cases (`docs/hand_calcs/s08_sweep.py`): the §4 worked example, x = patch connector loss (`channel[2].loss_max`) from 0 to 2 dB, y = TX OMA (`tx.launch_oma_min`) from −1 to +1 dBm.

| (patch loss, TX OMA) | M_net |
| --- | --- |
| (1.0 dB, 0 dBm), the design point | +0.4992 dB |
| (2.0 dB, 0 dBm) | −0.5008 dB |
| (0 dB, +1 dBm) | +2.4992 dB |

Slope −1 dB per dB of patch loss, +1 dB per dB of TX OMA.

## 9. Multi-lane tray

A tray is N lanes, each a §3 link, evaluated independently.

```
M_tray        = min_k M_net,k
verdict_tray  = EXCLUDED  iff  any lane is EXCLUDED
deciding lane = the excluded lane with the smallest margin if any lane is excluded,
                otherwise the lane with the smallest margin; ties go to the lowest index
```

Lanes are indexed from 0 in request order, like `channel[i]`. A tray has 1 to 1024 lanes.

Property: adding a lane never raises M_tray (a minimum over a superset).

Why: a tray ships as a unit. One excluded lane makes the tray unusable at the modeled constraints, so the tray is only as good as its worst lane, and the report has to say which lane that is.

Hand case (`docs/hand_calcs/s09_tray.py`): 8 copies of the §4 worked example, lane 5 (index 5) with its patch connector at 2.0 dB: lane margins +0.4992 dB except lane 5 at −0.5008 dB; M_tray = −0.5008 dB, deciding lane 5, EXCLUDED.

## 10. Upstream chain: TP2 derived (Milestone 2)

The §2 upstream elements, from the laser to TP2, replace the fixed TP2 input when a chain is given.

```
P_TP2,avg [dBm] = P_laser,avg − L_laser_fiber − L_couple − 10·log10(N) − L_excess − L_mod − L_out
P_TP2,OMA [dBm] = P_TP2,avg + 10·log10(2·(ER − 1)/(ER + 1)),   ER linear (the §3 OMA formula)
max fan-out     = the largest N ≥ 1 for which the link is NOT_EXCLUDED, found by search
```

- P_laser,avg: average laser power per output fiber; L_laser_fiber: laser fiber and connector to the PIC; L_couple: fiber-to-PIC coupling; 10·log10(N): ideal 1:N split; L_excess: split excess loss; L_mod: modulator insertion loss; L_out: output coupler to TP2; ER: modulator extinction ratio. All dB values ≥ 0, N an integer ≥ 1, ER > 0 dB.
- Losses are subtracted in the order written. M_net falls monotonically with N, so the search stops at the first excluded N. If N = 1 is already excluded, the max fan-out is 0.
- The derived TP2 is INFERENCE (computed from its parents); the chain inputs keep their own provenance.

Why: in co-packaged optics the laser is external and shared, so TP2 is not a free input but what is left of the laser power after the split and the modulator. Deriving it exposes the fan-out limit: each doubling of N costs 10·log10(2) = 3.0103 dB of margin.

Hand case (`docs/hand_calcs/s10_upstream.py`; all SYNTHETIC): laser 20 dBm average, laser fiber and connector 0.5 dB, coupling 1.5 dB, excess 0 dB, modulator IL 4.0 dB, output coupler 1.5 dB, ER 4 dB, the §4 channel (4.0008 dB), S_RX −6 dBm OMA, R 1.5 dB. Tolerance 1e-4.

| N | P_TP2,avg | P_TP2,OMA | M_net | Verdict |
| --- | --- | --- | --- | --- |
| 16 | +0.4588 dBm | −0.1911 dBm | +0.3081 dB | NOT_EXCLUDED |
| 17 | +0.1955 dBm | −0.4544 dBm | +0.0448 dB | NOT_EXCLUDED |
| 18 | −0.0527 dBm | −0.7026 dBm | −0.2034 dB | EXCLUDED |

Max fan-out: 17.

## 11. Statistical budget and yield

Loss elements may carry a normal distribution (SYNTHETIC) in addition to their worst-case maximum.

```
L_i ~ N(μ_i, σ_i²), independent; elements without a distribution stay at L_i,max
M_mean   = M_net with every distributed L_i at μ_i
σ_total  = sqrt(Σ σ_i²)
yield    = P(M_net ≥ 0) = Φ(M_mean / σ_total),   Φ the standard normal CDF
M_kσ     = M_mean − k·σ_total
```

- Monte Carlo draws every distributed L_i from a seeded generator and evaluates M_net per sample with the §3 expression; the Monte Carlo yield is the fraction of samples with M_net ≥ −ε and must reproduce the analytic yield. Samples are not truncated at 0 dB, so that they match the analytic model.
- With σ_total = 0 the yield is 1 if M_mean ≥ −ε and 0 otherwise, and z = M_mean/σ_total is undefined (reported as null).
- The result is labeled "statistical, assumption-dependent". It never changes the worst-case verdict, which §3 decides with every L_i at L_i,max.

Why: worst-case design over-provisions when connectors stack, because every connector at its maximum at once is rare. Independence and normality are assumptions: real connector loss is non-negative and skewed, so the normal tails are approximate, and correlated losses (one bad batch of ferrules) would widen σ_total beyond the root-sum-square.

Hand case (`docs/hand_calcs/s11_yield.py`): the §4 worked example with the three matings (μ = 1.5, 1.0 and 1.5 dB) each σ = 0.2 dB, fiber fixed. σ_total = 0.34641 dB, z = 1.44107, yield = 0.92522, M_3σ = −0.54003 dB. A seeded Monte Carlo with 10^6 samples lands within 0.002 of 0.92522 (its standard error is 0.00026).

## 12. Draft IEEE 802.3dj 200G DR budget

Every value in this section is PROPOSED_STANDARD: IEEE P802.3dj is a draft (D3.2 in its second Standards Association recirculation ballot, simms2026_3dj_tt), not an approved standard. The draft's numbers can still change; dawe2026_3dj_er199 is an open comment that would change four of them (below).

### 12.1 The 200GBASE-DR1 link budget as an OICD link

| Quantity | Draft value | Source |
| --- | --- | --- |
| Signaling | 106.25 GBd PAM4, RS(544,514) (FECo) | welch2023_3dj_baseline |
| Lane wavelengths, TX and RX | 1304.5 to 1317.5 nm | welch2023_3dj_baseline |
| TX OMAouter (min) | −1 + max(TECQ, TDECQ) dBm | johnson2025_3dj_mpidgd |
| TDECQ (max), TECQ (max) | 3.4 dB, 3.4 dB | welch2023_3dj_baseline, simms2026_3dj_tt |
| Extinction ratio (min) | 3.5 dB | welch2023_3dj_baseline, dawe2026_3dj_er199 |
| RX sensitivity (OMAouter, max) | −4.3 + TECQ dBm for 0.9 dB ≤ TECQ ≤ SECQ; −3.4 dBm below | welch2023_3dj_baseline, dawe2026_3dj_er199 |
| Channel insertion loss (max) | 3.0 dB, reduced by up to 0.5 dB by reflectances (12.2) | johnson2025_3dj_mpidgd |
| Allocation for penalties | 3.7 dB, including MPI 0.1 dB and DGD 0.2 dB | johnson2025_3dj_mpidgd |
| Power budget (for max TDECQ) | 6.7 dB | johnson2025_3dj_mpidgd |
| Operating distance; ORL tolerance; TX and RX reflectance | 500 m; 21.4 dB (15.5 dB for DR1); −26 dB | welch2023_3dj_baseline |

Mapping onto §3 (`profiles/ieee_dr_200g.json`):

```
P_TP2,OMA = −1 + 3.4                    = 2.4 dBm   (TX OMAouter min at max TDECQ)
S_RX      = −4.3 dBm                                (the sensitivity line −4.3 + TECQ at TECQ = 0)
Σ L       = 3.0 dB                                  (channel insertion loss)
Σ Π       = TDECQ 3.4 + MPI 0.1 + DGD 0.2 = 3.7 dB  (the draft's allocation, named)
R         = 0 dB                                    (the draft budget leaves nothing unallocated)
power budget = P_TP2 − S_RX = 6.7 dB;  allocation for penalties = 6.7 − 3.0 = 3.7 dB
M_net     = (2.4 − 3.0 − (−4.3)) − 3.7 − 0 = 0 dB on paper
```

The TX and RX wavelength range 1304.5 to 1317.5 nm is written as TX 1311 ± 6.5 nm into an RX passband of 1304.5 to 1317.5 nm, so both clearances are 0 nm.

Expected (`docs/hand_calcs/s12_dr_budget.py`): power budget 6.7 dB, allocation for penalties 3.7 dB, M_net = 0 on paper. In float, in the §3 order, M_net = −4.44e-16 dB, so the test asserts NOT_EXCLUDED and |M_net| < 1e-9: a second T04-type trap that only the ε of §3 resolves.

Why: an independent check of the engine against a budget written by others. The draft is built to close at exactly 0 dB with TDECQ at its maximum, so the engine must reproduce 0, not a rounding error of either sign.

Caveats:
- S_RX = −4.3 dBm is the intercept of the sensitivity line. The draft caps the receiver requirement at −3.4 dBm for TECQ below 0.9 dB, so −4.3 dBm is the reference the power budget is defined against, not a sensitivity a receiver must reach with an ideal transmitter.
- TDECQ enters as a named penalty because the TX OMA is taken at maximum TDECQ, as in the draft's "power budget (for max TDECQ)".
- Open comment R2-199 (dawe2026_3dj_er199) would set ER min 3 dB, sensitivity −4.5 + TECQ, budget 6.9 dB and penalties 3.9 dB (MPI up to 0.3 dB). Its outcome is not in any source read here, so the profile keeps the D3.x values.

### 12.2 Maximum channel insertion loss versus discrete reflectances (Table 180-12)

`max_channel_il(n_refl_45_35, n_refl_55_45)`: rows count the reflectances in (−45, −35] dB, columns those in (−55, −45] dB (johnson2025_3dj_mpidgd; unchanged in dawe2026_3dj_er199). "—" is not supported. Counts beyond the table are not supported either; negative counts are invalid input.

| (−45, −35] \ (−55, −45] | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 3.0 | 3.0 | 3.0 | 3.0 | 3.0 | 3.0 | 2.9 | 2.9 | 2.9 |
| 1 | 3.0 | 3.0 | 3.0 | 2.9 | 2.9 | 2.9 | 2.9 | 2.8 | 2.8 |
| 2 | 2.9 | 2.9 | 2.9 | 2.8 | 2.8 | 2.8 | 2.7 | 2.7 | 2.7 |
| 3 | 2.8 | 2.8 | 2.7 | 2.7 | 2.7 | 2.6 | 2.6 | 2.6 | 2.6 |
| 4 | 2.7 | 2.6 | 2.6 | 2.6 | 2.5 | 2.5 | 2.5 | 2.5 | — |
| 5 | 2.5 | 2.5 | 2.5 | — | — | — | — | — | — |
| 6 | — | — | — | — | — | — | — | — | — |

Expected: (0, 0) 3.0 dB; (0, 6) 2.9 dB; (2, 3) 2.8 dB; (4, 4) 2.5 dB; (5, 0) 2.5 dB; (4, 8) and (6, 0) not supported.

Why: in the draft, reflections and loss trade against each other. More reflectances mean more MPI, which the draft pays for with less allowed insertion loss instead of a larger MPI allocation.

### 12.3 Multipath interference: worst-case bound

From bhatt2016_mpi, for PAM-m with extinction ratio E (linear), transmitter, receiver and connector reflectances Rt, Rr, Rc (linear, from dB as 10^(R_dB/10)) and n connectors:

```
S       = √(Rt·Rr) + n·√(Rt·Rc) + n·√(Rr·Rc) + n(n − 1)/2 · Rc
x       = (m − 1) · 4 · S · E/(E − 1)
Π_MPI   = −10·log10(1 − x)  dB;   invalid input if x ≥ 1 (the bound diverges)
```

The four terms count the reflection pairs: TX–RX, TX–connector, RX–connector and connector–connector. Every interferer is assumed at the highest PAM level, coherent, antipodal and co-polarized with the victim.

Expected (`docs/hand_calcs/s12_dr_budget.py`): the source's example, PAM4 (m = 4), ER 6 dB, Rt −20 dB, Rr −26 dB, Rc −35 dB: n = 2, 4, 6 → 0.8142, 1.4378, 2.3137 dB (the source prints 0.81, 1.44, 2.31).

Why: MPI is the penalty a BiDi link and a dense connector plant both have to pay, and it needs a closed form the engine can evaluate. This form is a deterministic worst-case bound. IEEE allocates MPI at the 1e-6 cumulative probability point of a Monte Carlo of random phases (anslow2017_drrefl, used again for the Table 180-12 penalties in johnson2025_3dj_mpidgd), so the bound is conservative: it overstates the draft's own MPI allocation.

### 12.4 Reflection crosstalk in BiDi links

From bhatt2001_bidixtalk, for a single-wavelength BiDi link with a non-WDM coupler, NRZ and a receiver threshold adjusted for the crosstalk: the local transmitter's light reflected at the fiber interface reaches the local receiver.

```
T       = 10^(−IL/10)        channel transmission, IL the channel insertion loss in dB
R       = 10^(−RL/10)        reflection, RL the return loss at the interface in dB
Π_xtalk = 10·log10(T/(T − R))  dB;   invalid input if R ≥ T
source rule: RL ≥ IL + 5 dB keeps Π_xtalk below about 1.65 dB
```

Two-wavelength extension (INFERENCE, not in the source): with a diplexer that isolates the receiver from the local transmitter's wavelength by I dB, the reflected light is attenuated by I before the photodiode, so R = 10^(−(RL + I)/10). With I = 0 this is the source's formula.

Expected (`docs/hand_calcs/s12_dr_budget.py`): the source's example IL 7 dB, RL 12 dB → 1.6509 dB (source ≈ 1.65). Extension: IL 3 dB, RL 15.5 dB (the draft DR1 ORL tolerance), I 0 → 0.2514 dB; I 25 dB (SYNTHETIC) → 0.000772 dB.

Why: a BiDi link puts its own transmitter's reflections into its receiver, so it has to carry a crosstalk penalty that a duplex link does not. The extension shows why the wavelength diplexer matters: 25 dB of isolation removes the penalty almost entirely. Its form assumes the reflected light is suppressed like any out-of-band light, which holds only as far as the diplexer isolation does; the source's derivation (NRZ, threshold adjustment) is not re-derived for PAM4.

## 13. Microring and WDM link physics

Sources, all opened 2026-10-18: hu2025_arxiv (photon-lifetime bandwidth), geravand2025_mrm (its caution), decort2011 (resonance shift), frey2006_dndt (silicon dn/dT), xu2014_thermo (a measured ring drift), sun2015_nature (precedent: microring WDM optical I/O on a processor chip), andre2000_xtalk (an open source for the alternative crosstalk form) and bogaerts2012_mrr (review, abstract only). Every relation here is a model of a generic silicon microring; nothing in this section is a Lightmatter specification.

### 13.1 Ring relations

```
f0         = c/λ0
L          = π·D                                    (circumference of a ring of diameter D)
FSR_f      = c/(n_g·L),   FSR_λ = λ0²/(n_g·L)       (n_g the group index)
FWHM       = f0/Q_L                                 (Q_L the loaded quality factor)
T(Δ)       = Σ_{k=−50}^{50} 1/(1 + (2(Δ − k·FSR_f)/FWHM)²)   drop-port power, Δ = f − f_res
f_ph       = FWHM = f0/Q_L                          (photon-lifetime bandwidth)
Δλ/λ0      = Δn_eff/n_g                             (decort2011)
Δλ_heater  = η·P                                    (heater efficiency η in nm/mW)
dλ/dT      = λ0·(dn/dT)/n_g                         (mode taken fully in silicon: an upper bound)
```

- The drop port is a Lorentzian of width FWHM, repeated every FSR; the sum over 101 resonance orders (k = −50 … 50) captures the images that land on other channels (13.6). The sum approximates a ring's Airy response and peaks slightly above 1, by Σ_{k≠0} 1/(1 + (2k·FSR/FWHM)²): 0.1% (0.0047 dB) at Q_L 3500 and FSR 1.8 THz. The same tails make a single-Lorentzian and an image-summed leakage differ in the fifth decimal.
- Lifetime caveat: Q = ω0·τ with τ the energy (photon) lifetime, so f_ph = 1/(2πτ) = f0/Q, the form hu2025_arxiv gives (≈ c/(λQ)). The field amplitude decays with 2τ; a two-pole model written with the field lifetime, as in geravand2025_mrm, gives f0/(2Q), a factor of 2 apart. geravand2025_mrm also warns that this two-pole estimate "is often misleading" because it ignores detuning. OICD therefore uses FWHM = f0/Q_L only as the filter width for crosstalk and in the SYNTHETIC design-window rule of 13.3, never as a predicted electro-optic bandwidth.
- Silicon dn/dT = 1.94e-4 /K at 1.3 µm and 295 K (frey2006_dndt); with n_g = 3.5343 (13.8) this gives dλ/dT = 1310 × 1.94e-4/3.5343 = 0.0719 nm/K, the same order as the 77 pm/K measured for an 11 µm silicon ring in the C band (xu2014_thermo). The confinement of the mode in silicon is not modeled, so this is an upper bound.

### 13.2 WDM crosstalk penalty (INFERENCE)

```
X        = Σ_{m ≠ n, co-directional} T_n(f_m)          leakage of the other channels into ring n's drop port
Π_xt     = −10·log10(1 − k·X),   k = 1 for NRZ, k = 3 for PAM4;   invalid input if k·X ≥ 1
Π_alt    = 10·log10(1 + X)       (andre2000_xtalk, reported alongside)
```

Why the primary form: incoherent leakage with every interferer at its top level and a fixed decision threshold closes the eye by X times the top level. An NRZ eye (infinite extinction) is the full OMA wide, so its opening falls to (1 − X); each PAM4 eye is OMA/3 wide, so the same leakage closes it three times as much, (1 − 3X). This worst-case form is OICD's model (INFERENCE). The alternative 10·log10(1 + X) is the heterodyne crosstalk penalty of andre2000_xtalk (their eq. 8), derived for NRZ with infinite extinction and a decision level adjusted to the crosstalk; it is smaller because the threshold follows the crosstalk. Agrawal's textbook treatment was not opened in this run.

### 13.3 Design window (SYNTHETIC rules, adjustable in the UI)

```
neighbor rejection T(Δ) ≤ 10^(XT/10), XT = −15 dB:  Q_L ≥ Q_min = f0·√(10^(−XT/10) − 1)/(2Δ)
bandwidth f0/Q_L ≥ b·B, b = 0.75, B the symbol rate: Q_L ≤ Q_max = f0/(b·B)
window open  iff  Q_min ≤ Q_max
```

Δ is the spacing to the nearest co-directional neighbor. Both rules are assumptions, not physics: −15 dB of single-neighbor rejection and a filter at least 0.75 of the symbol rate wide.

### 13.4 Thermal tuning

```
required tuning = laser accuracy (±20 GHz as λ²·Δf/c) + fabrication offset (SYNTHETIC ±1 nm) + dλ/dT·ΔT
worst-case range = one co-directional channel spacing with barrel shifting; up to one FSR without
heater power     = range/η
```

Heaters only red-shift a ring. With barrel shifting, a ring locks to the nearest channel on its heater side and the electrical lanes are rotated to match, so no ring ever tunes more than one co-directional spacing. Without it, a ring must reach its assigned channel, which can take up to one FSR. The report also flags when the required tuning exceeds the worst-case range.

### 13.5 Guide grid (INFERENCE)

```
f_n = c/1310 nm + (n − 7.5)·200 GHz,   n = 0 … 15
even n: grid A; odd n: grid B   (two 400 GHz grids interleaved at 200 GHz)
```

Lightmatter says "centered at 1310 nm", two 400 GHz grids interleaved at a 200 GHz offset and ±20 GHz accuracy, but gives no channel frequencies, so this grid is OICD's inference.

### 13.6 Aliasing and the worst receive channel

A ring on channel n with FSR F has images at n ± j·F/200 GHz (j = 1, 2, …). An image on a co-directional channel adds that channel's full power to X (13.2). An image on a counter-directional channel (a local transmitter, travelling the other way) does not drop that channel's outbound light, which couples to the ring's other circulation; backscatter into the forward circulation is the residual path and is NOT_EVALUATED. The local transmitter's inbound reflections, however, travel with the signal and are dropped like signal, so they enter the reflection crosstalk of §12.4 weighted by the ring:

```
X_r     = Σ_{m local transmit} T_n(f_m)
Π_refl  = 10·log10(T/(T − R·X_r)),   T = 10^(−IL/10), R = 10^(−RL/10)
```

Worst receive channel: the largest Π_xt + Π_refl. Totals within 1e-6 dB are ties (truncating the image sum at k = ±50 moves physically identical channels by about 1e-8 dB), broken by the distance to the grid centre (the channel with neighbors on both sides), then by the lower index.

### 13.7 BiDi link model

Each direction is a §3 link. TP2 is the TX engine output before its diplexer and TP3 the RX engine input after its diplexer, so both diplexers are loss elements:

```
channel   = TX-end diplexer IL + fiber (length × α) + connectors + RX-end diplexer IL
penalties = reflection crosstalk (§12.4, from the fiber-plus-connector IL, the return loss and the
            diplexer isolation) + MPI (§12.3) + co-directional WDM crosstalk (§13.2) + named extras
α         = 0.40 dB/km at most from 1310 to 1625 nm for G.652.D cable (itut_g652_2024)
link NOT_EXCLUDED iff both directions are; margin = the smaller direction margin
minimum TX OMA of a direction = S_RX + Σ Π + R + Σ L   (the launch at which its M_net = 0)
crosstalk power at a receiver  = 10^(P_TX,local,OMA/10) · R  mW   (R of §12.4, with isolation)
```

The crosstalk power is the local transmitter's light that reaches the receiver by reflection, in the same OMA terms as the signal's power at TP3 (§3 power_mw). Why: the explorer's ghost pulse shows it next to the signal pulse. The §12.4 penalty assumes, as its source does, that the local and remote transmitters launch the same OMA; the crosstalk power uses the local transmitter's own OMA.

Each direction's TX wavelength range must also sit inside its own receiver's passband (§3). G.652 notes that its attenuation values should not be applied to short jumper, indoor or drop cables (IEC 60794-2-11, cited there and not read, gives 1.0 dB/km or less for indoor cable); at the metre lengths inside a rack the difference is below 0.01 dB.

### 13.8 Hand cases (`docs/hand_calcs/s13_ring_wdm.py`)

| Case | Expected |
| --- | --- |
| f0 at 1310 nm | 228.8492 THz |
| Q_L 3500 (lm_ofc25_talk): FWHM | 65.3855 GHz |
| one neighbor at 400 GHz; at 200 GHz | −21.781 dB; −15.846 dB, so interleaved BiDi gains 5.935 dB of isolation |
| two nearest neighbors at 400 GHz (single Lorentzian, images excluded) | X400 = 0.013272 → NRZ 0.0580 dB, PAM4 0.1764 dB |
| two nearest neighbors at 200 GHz | X200 = 0.052050 → NRZ 0.2321 dB, PAM4 0.7373 dB |
| alternative form 10·log10(1 + X) | 0.0573 dB (X400), 0.2204 dB (X200) |
| FSR 1.8 THz (lm_ofc25_paper) | 10.3037 nm = 9 slots of 200 GHz |
| implied n_g for a 15 µm diameter (lm_hc25_m1000) | 3.5343 (cross-source INFERENCE) |
| window 56 GBd at 200 GHz | [3166.0, 5448.8], open, Q 3500 inside |
| window 56 GBd at 400 GHz | [1583.0, 5448.8], open |
| window 106.25 GBd at 200 GHz | [3166.0, 2871.8], closed |
| window 106.25 GBd at 400 GHz | [1583.0, 2871.8], open, Q 3500 outside |
| heater at 0.44 nm/mW (lm_ofc25_paper) | 200 GHz = 1.1449 nm = 2.6020 mW; 400 GHz 5.2039 mW; full FSR 23.4176 mW |
| unique channel within one FSR for 16 × 200 GHz = 3.2 THz | L ≤ c/(n_g·3.2 THz), so R ≤ 3.5501 µm at n_g 4.2 (SYNTHETIC n_g) |
| Guide grid | λ_0 1318.6431 nm, λ_15 1301.4695 nm, outer span 17.1736 nm; ±20 GHz = ±0.11449 nm |
| ring on channel 0 with FSR 1.8 THz | image on channel 9 (grid B, counter-directional) |

BiDi link model case (`docs/hand_calcs/s13_ring_wdm.py`): an L20-style BiDi pair on the draft DR budget of §12.1. TX OMA 2.4 dBm, diplexer IL 1.0 dB at each end (SYNTHETIC), 0.5 km of fiber at 0.4 dB/km (0.2 dB), one 0.5 dB connector (SYNTHETIC), S_RX −4.3 dBm, TDECQ 3.4 dB and MPI 0.1 dB as named extras, return loss 15.5 dB and diplexer isolation 25 dB (SYNTHETIC), R = 0. The reflection crosstalk at channel IL 0.7 dB is 0.000455 dB, so each direction has M_net = 0.49955 dB. Direction A at 1311 nm (δ = 0) clears the 1304.5 to 1317.5 nm passband by 6.5 nm on each side; direction B at 1331 nm misses it by 13.5 nm, so the link is EXCLUDED on wavelength alone. Power at TP3 −0.3 dBm OMA = 0.933254 mW; reflected local TX 2.4 dBm × 10^(−40.5/10) = 1.548817e-4 mW, 37.80 dB below the signal; with no diplexer isolation (I = 0) it would be 0.048978 mW.

Properties tested: crosstalk falls with spacing, the penalty rises with X, heater power is linear in the tuning.

## 14. Product twin

### 14.1 Method

The twin reconstructs a product from what its maker and others have published, and labels every number by where it came from. It is not Lightmatter's specification and is not affiliated with or endorsed by Lightmatter.

- **Facts** (`catalog/products/*.toml`, `[[fact]]`): a public statement with its exact quote, citation key and class (VENDOR_CLAIM, PEER_REVIEWED, THIRD_PARTY, PUBLISHED_SPEC or PROPOSED_STANDARD). `verified` is true only if the value was confirmed in the opened source in this run; otherwise the Appendix wording is kept and a note says why. A fact is a point (`value`) or a range (`lo`, `hi`); `bound` records whether the source says exact, approximately, at least (min) or at most (max). Non-numeric facts (a modulation format) carry no number.
- **Assumptions** (`[[assumption]]`): SYNTHETIC values with nominal, low, high and a rationale.
- **Derived nodes** (`[[derived]]`): INFERENCE. A registered formula (`oicd.twin.formulas`, never an evaluated string) of other nodes, with the formula's units checked against its inputs. Each carries a derivation string, e.g. "30 W / 6.4 Tbps = 4.6875 pJ/bit".
- **Intervals:** facts are points unless the source gives a range (nominal = the middle); assumptions span [low, high]. A derived node's [lo, hi] is the minimum and maximum of the node evaluated at its nominal point and at every corner of its interval-valued ancestors. This is exact when the node is monotone in each ancestor, which holds for every formula used here (products, quotients, sums, differences and logarithms of positive quantities). With more than 12 interval ancestors, 4096 seeded uniform samples replace the corners and the node is flagged.
- **Checks** (`[[check]]`): `consistent` compares two nodes in the same unit, gap = |a − b|/|b|; `bound` requires a ≥ b (b a "min" fact) or a ≤ b (b a "max" fact), each with tolerance rel_tol·|b|. A `bound` check against any other node states its `relation` (`le` or `ge`) explicitly, for requirements such as "grid span ≤ ring FSR".

```
CONSISTENT  if the gap is within tolerance (or the bound holds)
CONFLICT    otherwise, if a and b are both facts (two sources disagree)
TENSION     otherwise (a derived node or assumption, that is, a reading of ours, disagrees with a claim)
```

  Each outcome also reports whether the two intervals, widened by the tolerance, overlap: an overlap means some assumption inside its range would reconcile them.
- **Conflicts:** facts list the facts they contradict (`conflicts_with`). Both sides are carried downstream and shown side by side; neither is silently picked.
- **Hypotheses** (`[[hypothesis]]`): a named reading of an ambiguous claim that pins assumptions (`sets`). Alternatives share a `group`; at most one per group is applied. Re-evaluating the graph under each hypothesis gives the **support matrix**: hypothesis × check status, and for each hypothesis the checks it agrees with (CONSISTENT) and disagrees with.
- **Tornado:** for each derived node, each SYNTHETIC ancestor in turn at its low and high value, the others at nominal; bars sorted by swing |value(high) − value(low)|.

Why: reverse engineering mixes three kinds of number, what a source says, what we assume and what follows from both. Keeping them apart, with intervals and named readings, lets a reader see which conclusions depend on which assumption, and which public claims each reading agrees with.

Hand case (`docs/hand_calcs/s14_toy_graph.py`, the toy graph of `tests/data/catalog_toy`): power 30 W and rate 6.4 Tbps (facts), direction factor 1 (assumption, range 1 to 2), energy = 30 W / (factor × 6.4 Tbps):

| Quantity | Expected |
| --- | --- |
| energy at factor 1 (nominal) | 4.6875 pJ/bit |
| energy interval over factor 1 to 2 (corners) | 2.34375 to 4.6875 pJ/bit |
| check against a 5 pJ/bit claim, tolerance 10% | gap 6.25%, CONSISTENT |
| check against a 3.0 pJ/bit copy, tolerance 25% | gap 56.25%, TENSION (derived node involved) |
| the same two checks under the hypothesis factor = 2 | gap 53.125%, TENSION; gap 21.875%, CONSISTENT |
| two width facts 26.4 and 27.6 mm, tolerance 1% | gap 4.348%, CONFLICT (both facts) |
| tornado swing of the factor on the energy | 2.34375 pJ/bit |
| bound: 8 × 13 mW against a "minimum 100 mW" fact | 104 mW ≥ 100 mW, CONSISTENT |

With 13 interval ancestors the node is evaluated by Monte Carlo and flagged.

### 14.2 Passage L20

Facts (VENDOR_CLAIM unless marked): 6.4 Tbps each direction, 32 optical ports at 200 Gb/s per lane DR, 212.5 Gb/s PAM4 SerDes line rate, BiDi at 1311 and 1331 nm, TDP 30 W max (lm_pr_l20); "30W (3.0 pJ/bit)" (lm_pr_l20_bw only); "5 pJ/bit" (lm_web_l20, lm_yole_ofc26); 37.5 × 26.4 mm and 1827-ball BGA (lm_web_l20) against 37.5 × 27.6 × 4.55 mm (lm_yole_ofc26) and 2000-pin BGA (lm_pr_l20).

| Derived (INFERENCE) | Value | Check |
| --- | --- | --- |
| rate per port = 6.4 Tbps / 32 | 200 Gb/s | CONSISTENT with "200 Gbps per lane" |
| line/payload = 212.5/200 | 1.0625 | (the draft 802.3dj FEC and transcoding overhead) |
| energy, one direction = 30 W / 6.4 Tbps | 4.6875 pJ/bit | CONSISTENT with "5 pJ/bit" (pluggables also divide by one direction) |
| energy, both directions = 30 W / 12.8 Tbps | 2.34375 pJ/bit | |
| power that "3.0 pJ/bit" needs at 6.4 Tbps | 19.2 W | TENSION with 30 W; both sources kept |
| 1331 − 1311 | 20 nm = 3436.1 GHz | two adjacent CWDM channels (itut_g6942_2003), INFERENCE |
| clearances to the draft DR range 1304.5 to 1317.5 nm, δ = 0 (tolerance not disclosed) | 1311 nm: 6.5 nm each side; 1331 nm: −13.5 nm | 1311 passes, 1331 fails |
| lanes per laser fiber = 32/8 | 4 | |
| fiber reduction = 1 − 32/64 | 50% | CONSISTENT with "−50%" |
| volumes 37.5 × 27.6 × 4.55 vs 108.8 × 22.93 × 15.5 mm | 4709.25 vs 38669.15 mm³, 87.82% smaller | CONSISTENT with "~88%" |
| 18 × 6.4; 6 × 6.4 | 115.2 Tbps; 38.4 Tbps | CONSISTENT with "115.2 Tbps (18 x L20)" and "38 Tbps (6 x L20)" |
| savings 1 − 5/17; 1 − 5/20 | 70.59%; 75% | CONSISTENT with "Up to 75%" |

"DR compatible" cannot mean draft-DR wavelength compliance in both directions: 1331 nm lies 13.5 nm outside the draft range. That is an open question (INFERENCE), not a finding against the product: the phrase may refer to the electrical interface, the reach or one direction. The package-size and pin-count disagreements stay CONFLICTs, both sides carried.

Hypotheses: H_l20_one_dir (the energy figure divides by one direction: agrees with "5 pJ/bit") and H_l20_both_dirs (both directions: agrees with neither "5" nor "3.0" within 10%).

### 14.3 Passage M1000

| Derived (INFERENCE) | Value | Check |
| --- | --- | --- |
| 256 fibers × 448 Gb/s | 114.688 Tbps | CONSISTENT with 114 and 114.6 Tbps within 0.6% |
| 8 λ × 56 Gb/s | 448 Gb/s | CONSISTENT with 448 Gb/s per fiber |
| 1024 SerDes × 56 Gb/s × 2 | 114.688 Tbps | CONSISTENT with "Tx + Rx" |
| 16 buses × 2 × 8 tiles | 256 links = fibers | |
| 128 SerDes × 8 tiles | 1024 | CONSISTENT |
| 91 × 85 mm | 7735 mm² | CONSISTENT with the 7,735 mm² package |
| ceiling 4000 mm² × 1.4 W/mm² | 5.6 kW | against 1.5 kW delivered |
| 1.5 kW over 7735 mm²; over 4000 mm² | 0.194 W/mm²; 0.375 W/mm² | so ">1.4 W/mm²" reads as a local or capability figure (INFERENCE) |
| I/O power at 2.3 pJ/bit | 263.78 W if the rate counts Tx + Rx (17.6% of 1.5 kW); 131.89 W per direction | hypotheses H_m1000_txrx and H_m1000_per_dir |
| λ-channels = 256 × 8 | 2048, one ring per channel (INFERENCE) | |
| heaters, worst case with barrel shifting at 0.44 nm/mW | 2048 × 2.6020 mW = 5.329 W | assumes the M1000 rings resemble the OFC 2025 rings (INFERENCE) |

The ISES 2025 slide's "800 Gbps / fiber (Tx+Rx)" against 448 Gb/s stays a CONFLICT. The physics evaluation also shows why barrel shifting matters: with ±20 GHz laser accuracy, a SYNTHETIC ±1 nm fabrication offset and a 10 K swing, a ring needs 1.83 nm of tuning, more than one 200 GHz spacing (1.145 nm); without barrel shifting the worst case is a full FSR, 23.4 mW per ring and about 48 W for 2048 rings.

### 14.4 Passage L200 and L200X

| Derived (INFERENCE) | Value | Check |
| --- | --- | --- |
| L200: 320 SerDes × 50 Gb/s payload × 2 | 32 Tbps | CONSISTENT with "32 Tbps total (Tx+Rx)"; 50 Gb/s payload on a 56 Gb/s line (INFERENCE) |
| L200X: 320 × 100 × 2 | 64 Tbps | CONSISTENT with "64 Tbps total (Tx+Rx)" |
| fibers 32/0.8; 64/1.6 | 40; 40 | |
| 4 × 64 Tbps | 256 Tbps per package | CONSISTENT with the product page |
| 32 Tbps / 40 | 800 Gb/s per pluggable equivalent | |

NRZ (lm_pr_l200) against PAM4 (lm_web_l200) stays a CONFLICT.

### 14.5 16λ BiDi link (EVK50, OFC 2026)

16 × 50 Gb/s = 800 Gb/s per fiber, 8 × 50 = 400 Gb/s each way. Channel plan: the §13.5 grid, one direction on even n and the other on odd n (the OFC 2026 link diagram shows laser module A on λ0, λ2 … λ14 and module B on λ1, λ3 … λ15); the end analysed here receives on odd n. Ring model: Q_L 3500 and FWHM 65.3855 GHz for every channel, images k = −50 … 50 (§13.6). The rings' FSR is not disclosed, so two hypotheses are carried:

- H_fsr18: the OFC 2025 ring, FSR 1.8 THz = 9 slots. Seven of eight receive rings (all but channel 7) then have an image exactly on a local transmit channel, and co-directional channels 8 or 10 slots away sit one slot from an image.
- H_fsr32: FSR 3.2 THz, R ≤ 3.5501 µm at n_g 4.2 (§13.8).

Worst receive channel (§13.6), IL 3 dB (vendor) and RL 15.5 dB (SYNTHETIC, the draft DR1 ORL tolerance):

| Hypothesis | Channel | Co-directional X | NRZ penalty | Reflected X_r | Reflection crosstalk |
| --- | --- | --- | --- | --- | --- |
| H_fsr18 | 3 | 0.081869 | 0.3710 dB | 1.082941 | 0.2729 dB |
| H_fsr32 | 7 | 0.021508 | 0.0944 dB | 0.064485 | 0.0158 dB |

A 1.8 THz ring erases most of the interleaving gain (worst-channel co-directional crosstalk 5.8 dB higher), so the 16λ BiDi link wants an FSR of at least 3.2 THz: the headline ring inference, labeled INFERENCE. MPI (§12.3, bhatt2016_mpi) with NRZ m = 2, ER 6 dB, Rt = Rr = −26 dB, Rc = −45 dB and n = 6 (all SYNTHETIC) = 0.1503 dB.

TX OMA is not public, so the twin reports the minimum TX OMA the link needs, S_RX + IL + penalties, with S_RX = −9 dBm OMA (lm_ofc25_talk, a cross-source assumption): H_fsr18 −5.2059 dBm, H_fsr32 −5.7395 dBm. The vendor's BER < 1e-9 without FEC stays a VENDOR_CLAIM, not something OICD checks.

### 14.6 Guide, Guide 1 and Guide DR

| Derived (INFERENCE) | Value | Check |
| --- | --- | --- |
| Guide 1: 8 × 13 mW | 104 mW | CONSISTENT with "≥100 mW/fiber" (bound) |
| 16 fibers × 100 mW | 1.6 W | CONSISTENT (single package) |
| 32 × 100 to 110 mW | 3.2 to 3.52 W | CONSISTENT with 3.2–3.5 W (stacked); 110 mW per fiber is SYNTHETIC |
| 100 Tbps / 4 modules | 25 Tbps per module | BOUND OK against "up to 51.2" |
| 100 Tbps / 18 ELSFP | 5.556 Tbps per ELSFP | |
| Guide DR: 64 × 200 mW | 12.8 W | CONSISTENT with "12.8W total" |
| 256 lanes × 200 Gb/s | 51.2 Tbps | CONSISTENT |
| 256/64 | 4 lanes per laser fiber | |
| 200 mW / 4 lanes | 50 mW = 16.99 dBm per lane before PIC losses (even split, INFERENCE) | |
| 200 mW | 23.01 dBm = ELSFP UHP class (oif_elsfp_02), 1.49 dB under the 24.5 dBm Hazard Level 1 limit | |
| Guide 1: 13 mW | 11.14 dBm ≈ ELSFP LP class | |

Fan-out: §10 with 200 mW per fiber, the §10 chain losses (0.5, 1.5, 4.0 and 1.5 dB, excess 0, ER 4 dB; SYNTHETIC) and the §12 DR budget:

| N | P_TP2,avg | P_TP2,OMA | M_net | Verdict |
| --- | --- | --- | --- | --- |
| 4 | 9.4897 dBm | 8.8398 dBm | +6.4398 dB | NOT_EXCLUDED |
| 17 | 3.2058 dBm | 2.5559 dBm | +0.1559 dB | NOT_EXCLUDED |
| 18 | 2.9576 dBm | 2.3077 dBm | −0.0923 dB | EXCLUDED |

Max fan-out 17. So 4 lanes per fiber leaves about 6.4 dB unallocated in this chain: either the real chain loses about 6 dB more (H_chain_lossier), or the laser is provisioned for aging, temperature and TDECQ corners (H_laser_headroom). Both are carried (INFERENCE).

### 14.7 OCP 2026 trays

204.8/8 = 102.4/4 = 25.6 Tbps per engine (CONSISTENT across the two trays) = 4 × the L20's 6.4 Tbps per direction, so each tray engine carries four L20s' worth of lanes; the release does not name the engine (INFERENCE). Hypotheses for the switch tray's 204.8 Tbps:

- H_dir (per direction): 1024 lanes, 4 Guide DR; agrees with lm_pr_guidedr's "four Guide DR modules … 204.8 Tbps".
- H_agg (aggregate): 512 lanes per direction, 2 Guide DR; agrees with counterpoint_ocp26's "two" and ine_ocp26's "aggregate".

The XPU tray under H_dir: 512 lanes, 2 Guide DR, which agrees with Counterpoint's two for that tray. Tray height 1RU against 2U: both carried (H_xpu_1u, H_xpu_2u). The support matrix shows each hypothesis against each claim.

### 14.8 Scale-up pod example (lm_pr_cpx, lm_hoti26)

```
duplex fibers = XPUs × lanes per XPU × 2 = 512 × 128 × 2 = 131,072     (≈ "about 130,000", 0.8%)
BiDi fibers   = 65,536    →  implies 25.6 Tbps per XPU per direction (128 × 200 Gb/s), CONSISTENT with the XPU tray
HOTI26 "32 Tbps / XPU": 512 × 160 × 2 = 163,840 (26% off)              → TENSION
mean fiber length saved = 200 miles / 65,536 = 4.9113 m;  150 miles → 3.6835 m
mating plane with 16-fiber ferrules (SYNTHETIC; PRIZM TMT starts at 16): 65,536/16 = 4,096 connectors
"~16,000 fewer connectors" ≈ 4 × 4,096 = 16,384  →  about two mated pairs per path (INFERENCE under that assumption)
HOTI26 "20,000" → TENSION
```

Under H_pod_32 the same arithmetic gives 163,840 fibers and 20,480 connectors, so HOTI26's "20,000" becomes CONSISTENT: each source is internally consistent with its own per-XPU bandwidth (the CPX release with 25.6 Tbps, HOTI26 with 32 Tbps).

### 14.9 Reference rack OICD-R64 (an OICD design: SYNTHETIC, never Lightmatter's)

- Frame: ORv3, 600 × 1068 × 2286 mm, 44 OU of 48 mm (ocp_orv3_meta). 8 switch trays (1 OU), 16 XPU trays (2 OU under H_2U, 1 OU under H_1U), 2 power shelves (537 × 46.2 × 867.5 mm, ocp_orv3_hpr72): 42 OU (H_2U) or 26 OU (H_1U).
- Single tier: each XPU sends 16 lanes to each switch tray (H_dir): 64 XPUs × 128 lanes = 8192 links = 8 × 1024. BiDi fibers 8192 against duplex 16,384. TX lanes 16,384 → 64 Guide DR (2 per XPU tray, 4 per switch tray).
- Worst path: XPU engine → vClick → 0.5 m tray fiber → PRIZM TMT blind mate (0.5 dB, corning_tmt_lan3581) → 3 m rack fiber → switch-tray connector (SYNTHETIC 0.5 dB, TMT class) → 0.5 m → vClick → switch engine; 4 m of fiber at 0.4 dB/km = 0.0016 dB.
- Reference-plane hypotheses: H_vclick_channel (the vClick is a mated connection between TP2 and TP3, per §2) and H_vclick_module (the engine's DR spec is defined after its vClick). With the §12 DR budget:

| Case | Channel IL | M_net | Verdict |
| --- | --- | --- | --- |
| vClick 1.5 dB in the channel | 4.0016 dB | −1.0016 dB | EXCLUDED |
| vClick 1.0 dB (futurum_ocp26 "below 1 dB") in the channel | 3.0016 dB | −0.0016 dB | EXCLUDED |
| vClick in the module | 1.0016 dB | +1.9984 dB | NOT_EXCLUDED |

The reference-plane definition, not the physics, decides this rack.

- Rack yield with independent links: P(all 8192 pass) = y^8192; y = 0.9999 → 0.4408; y = 0.99999 → 0.9213; a 99% rack needs y ≥ 0.99999877 (z = 4.712σ one-sided). Statistical design at rack scale returns to about 4.7σ per link.
- Topology: single-tier radix = switch lanes / lanes per XPU per switch plane = 1024/16 = 64 XPUs per single-tier domain with these trays, against the OCP vision's flat domains of about 1,024 to 2,048 XPUs (ocp_osp_initiative_2026), which would need one lane per XPU per plane.

### 14.10 Hand cases

All numbers in §14.2 to §14.9 are printed by `docs/hand_calcs/s14_products.py` (the ring numbers of §14.5 by `s13_ring_wdm.py`), and the tests take them from this section.
