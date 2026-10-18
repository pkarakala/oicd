# Model card: optical link feasibility (Milestone 1)

Author: Pranav. Write this by hand before any code exists. Every blank (`____`) is yours to fill; the code and tests must match it.

## 1. Scope

What the model decides: whether a single point-to-point optical lane is **not excluded** by electrical, wavelength and optical-power constraints.
What it does not decide: BER, eye quality, dispersion, reflections, thermal behavior, reliability. These are listed as `NOT_EVALUATED`.

## 2. Reference planes

Draw the chain and define each plane in one sentence.

```
laser out ──► [laser fiber + connector] ──► PIC in ──► [split 1:N] ──► [modulator] ──► [out coupler] ──► TP2
TP2 ──► [connector] ──► [fiber] ──► [connector] ──► TP3 ──► [RX coupler] ──► PD
```

- TP2: ____ (where transmitter power is specified)
- TP3: ____ (where receiver sensitivity is specified)
- Which elements are inside the Milestone 1 budget (TP2 to TP3): ____
- Which elements are upstream and deferred to Milestone 2: ____

## 3. Equations

Power budget, worst case, OMA throughout:

```
P_TP3,OMA [dBm] = P_TP2,OMA,min [dBm] − Σ L_i,max [dB]
M_net [dB]      = P_TP3,OMA − S_RX,OMA,max − Σ Π_j − R
PASS  iff  M_net ≥ −ε,   ε = 1e-9 dB
```

OMA from average power (only for converting inputs, never mixed in the budget):

```
OMA = 2 · P_avg · (ER − 1) / (ER + 1),   ER linear
```

Wavelength compatibility (interval containment):

```
[λ_TX − δ_TX, λ_TX + δ_TX] ⊆ [λ_RX,min, λ_RX,max]
Δλ ≈ λ² Δf / c
```

Electrical compatibility: TX and RX match on (modulation, symbol_rate_gbd, lanes, fec). Line rate = symbol rate × bits per symbol.

Explain in your own words, two lines each:
- Why OMA and not average power: ____
- Why worst case and not typical: ____
- Why penalties Π_j are separate from reserve R: ____

## 4. Worked example (by hand)

Inputs: P_TP2 = 0 dBm OMA, losses = connector ____ dB + fiber ____ dB + connector ____ dB (sum 4.0 dB), S_RX = −6 dBm OMA, Π = 0, R = 1.5 dB.
P_TP3 = ____ dBm. M_net = ____ dB. Verdict: ____.

## 5. Test cases (expected values from your hand calculations)

| ID | What it tests | Key inputs | Expected |
| --- | --- | --- | --- |
| T01 | Nominal pass | 0 dBm, 4 dB, −6 dBm, R 1.5 | M = +0.5 dB, PASS |
| T02 | Nominal fail | 0 dBm, 5 dB, −6 dBm, R 1.5 | M = −0.5 dB, FAIL |
| T03 | Exact boundary | loss = 4.5 dB | M = ____, ____ |
| T04 | Boundary with non-representable floats | losses 0.1 + 0.2 + ... | ____ |
| T05 | Loss monotonicity | add one 0.5 dB connector | margin drops by exactly ____ |
| T06 | Named penalty | Π = 1.0 dB on T01 | M = ____, ____ |
| T07 | OMA/average mixing | TX average, RX OMA | raises error |
| T08 | Average to OMA conversion | P_avg = 0 dBm, ER = 4 dB | OMA = ____ dBm |
| T09 | Wavelength inside passband | 1310 ± 2 nm into 1300 to 1320 nm | ____ |
| T10 | Wavelength edge outside | 1318 ± 3 nm into 1300 to 1320 nm | ____ |
| T11 | Electrical mismatch | 106.25 GBd PAM4 vs 53.125 GBd PAM4 | ____ |
| T12 | Invalid physics | negative loss, 0 nm wavelength | rejected at schema |
| T13 | Provenance | every result lists source class of each input | ____ |
| T14 | Determinism | run twice | identical report |
| T15 | Not evaluated list | any link | lists BER, dispersion, reflections, thermal, reliability |

## 6. What would validate this model on real hardware

- Loss elements: ____ (instrument and method)
- TP2 OMA: ____
- Sensitivity: ____ (BER target and how measured)

## 7. Decision log

| Date | Decision | Why | Alternative rejected |
| --- | --- | --- | --- |
| 2026-10-18 | Budget in OMA | 200G/lane DR optics specify TX and RX in OMA | Average power: simpler but mixes quantities |
