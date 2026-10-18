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

What this shows: the 2 m of fiber contributes 0.0008 dB, 0.02% of the budget. At rack scale, connector count, not fiber length, sets the budget. The 0.4 dB/km figure is a typical single-mode value at 1310 nm, to be cited (ITU-T G.652) before it is used outside this example.

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
