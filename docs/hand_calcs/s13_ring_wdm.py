"""Hand calculations for model card §13 (microring and WDM link physics). Standard library only.

Ring drop-port response: Lorentzian with FWHM = f0/Q_L, periodic in the FSR (images k = -50..50).
Wavelength spans use the §3 approximation Δλ = λ²·Δf/c.
"""

from math import log10, pi, sqrt

C = 299_792_458.0
LAMBDA0_NM = 1310.0
F0_GHZ = C / (LAMBDA0_NM * 1e-9) / 1e9


def dlambda_nm(df_ghz, lam_nm=LAMBDA0_NM):
    return (lam_nm * 1e-9) ** 2 * df_ghz * 1e9 / C * 1e9


def lorentz(detuning_ghz, fwhm_ghz):
    return 1.0 / (1.0 + (2.0 * detuning_ghz / fwhm_ghz) ** 2)


def ring_drop(f_ghz, f_res_ghz, fwhm_ghz, fsr_ghz, images=50):
    return sum(
        lorentz(f_ghz - f_res_ghz - k * fsr_ghz, fwhm_ghz) for k in range(-images, images + 1)
    )


def xt_db(x, k):
    return -10 * log10(1 - k * x)


print(f"f0 at 1310 nm = {F0_GHZ / 1000:.4f} THz")
Q = 3500
fwhm = F0_GHZ / Q
print(f"Q {Q}: FWHM = {fwhm:.4f} GHz")
t400, t200 = lorentz(400, fwhm), lorentz(200, fwhm)
print(
    f"one neighbor at 400 GHz {10 * log10(t400):.3f} dB, at 200 GHz {10 * log10(t200):.3f} dB,"
    f" interleaving gain {10 * log10(t200 / t400):.3f} dB"
)
x400, x200 = 2 * t400, 2 * t200
print(f"X400 = {x400:.6f}: NRZ {xt_db(x400, 1):.4f} dB, PAM4 {xt_db(x400, 3):.4f} dB")
print(f"X200 = {x200:.6f}: NRZ {xt_db(x200, 1):.4f} dB, PAM4 {xt_db(x200, 3):.4f} dB")
print(
    f"alternative form 10·log10(1 + X): X400 {10 * log10(1 + x400):.4f} dB, "
    f"X200 {10 * log10(1 + x200):.4f} dB"
)

fsr = 1800.0
print(f"FSR 1.8 THz = {dlambda_nm(fsr):.4f} nm = {fsr / 200:.0f} slots of 200 GHz")
L_m = pi * 15e-6
print(f"implied n_g for a 15 um diameter ring: {C / (fsr * 1e9 * L_m):.4f}")

print("design windows [Q_min, Q_max]: crosstalk per neighbor <= -15 dB, f0/Q >= 0.75 x symbol rate")
q_min = {d: F0_GHZ * sqrt(10**1.5 - 1) / (2 * d) for d in (200, 400)}
for baud in (56, 106.25):
    q_max = F0_GHZ / (0.75 * baud)
    for d in (200, 400):
        state = "open" if q_min[d] <= q_max else "closed"
        inside = "inside" if q_min[d] <= Q <= q_max else "outside"
        print(f"  {baud} GBd at {d} GHz: [{q_min[d]:.1f}, {q_max:.1f}] {state}, Q 3500 {inside}")

eta = 0.44  # nm/mW
for df in (200, 400):
    print(f"heater: {df} GHz = {dlambda_nm(df):.4f} nm = {dlambda_nm(df) / eta:.4f} mW")
print(f"heater: full FSR {dlambda_nm(fsr):.4f} nm = {dlambda_nm(fsr) / eta:.4f} mW")
ng = 4.2
r_max = C / (ng * 3.2e12) / (2 * pi)
print(f"unique channel in one FSR for 16 x 200 GHz: R <= {r_max * 1e6:.4f} um at n_g {ng}")
print(f"laser accuracy +/-20 GHz = +/-{dlambda_nm(20):.5f} nm")

grid = [F0_GHZ + (n - 7.5) * 200.0 for n in range(16)]
lam = [C / (f * 1e9) * 1e9 for f in grid]
print(
    f"Guide grid: lambda_0 {lam[0]:.4f} nm, lambda_15 {lam[15]:.4f} nm, "
    f"span {lam[0] - lam[15]:.4f} nm"
)
print(
    "ring on channel 0 with FSR 1.8 THz: images on channels",
    [
        n
        for n in range(16)
        if n != 0 and abs(((grid[n] - grid[0]) / fsr) - round((grid[n] - grid[0]) / fsr)) < 1e-9
    ],
)

print("16-lambda BiDi, receive on odd n, transmit on even n, Q 3500, images k = -50..50")
il_db, rl_db = 3.0, 15.5
T, R = 10 ** (-il_db / 10), 10 ** (-rl_db / 10)
for name, fsr_h in (("H_fsr18", 1800.0), ("H_fsr32", 3200.0)):
    rows = []
    for n in range(1, 16, 2):
        x = sum(ring_drop(grid[m], grid[n], fwhm, fsr_h) for m in range(1, 16, 2) if m != n)
        xr = sum(ring_drop(grid[m], grid[n], fwhm, fsr_h) for m in range(0, 16, 2))
        rows.append((x, n, xr))
    x, n, xr = max(rows)
    pen_x = xt_db(x, 1)
    pen_r = 10 * log10(T / (T - R * xr))
    print(
        f"  {name}: worst channel {n}: X {x:.6f} -> NRZ {pen_x:.4f} dB; X_r {xr:.6f} -> "
        f"reflection crosstalk {pen_r:.4f} dB"
    )
    hits = [
        m
        for m in range(1, 16, 2)
        if any(abs(grid[e] - grid[m] - k * fsr_h) < 1e-6 for e in range(0, 16, 2) for k in (-1, 1))
    ]
    print(f"    receive rings with an image exactly on a local transmit channel: {hits}")

print("§13.7 BiDi link model case: L20-style pair on the draft DR budget")
fiber_db = 0.5 * 0.4
channel_il = fiber_db + 0.5  # fiber plus one connector, TP2 to TP3 between the diplexers
t_ch = 10 ** (-channel_il / 10)
r_eff = 10 ** (-(15.5 + 25.0) / 10)
refl = 10 * log10(t_ch / (t_ch - r_eff))
total_loss = 1.0 + fiber_db + 0.5 + 1.0
margin = ((2.4 - total_loss) - (-4.3)) - (refl + 3.4 + 0.1) - 0.0
print(
    f"  reflection crosstalk at IL {channel_il:.1f} dB: {refl:.6f} dB; "
    f"M_net {margin:.5f} dB per direction"
)
for name, lam in (("A", 1311.0), ("B", 1331.0)):
    print(
        f"  direction {name} at {lam} nm: lower clearance {lam - 1304.5:+.1f} nm, "
        f"upper clearance {1317.5 - lam:+.1f} nm"
    )
