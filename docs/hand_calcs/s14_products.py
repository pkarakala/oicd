"""Hand calculations for model card §14 (architecture twins and the reference rack).
Standard library only; never imports oicd. Every number the card quotes is printed here."""

from math import erfc, log10, sqrt

C = 299_792_458.0


def nm_to_ghz(lam_nm):
    return C / (lam_nm * 1e-9) / 1e9


def span_nm(df_ghz, lam_nm=1310.0):
    return (lam_nm * 1e-9) ** 2 * df_ghz * 1e9 / C * 1e9


def dbm(p_mw):
    return 10 * log10(p_mw)


print("§14.2 BiDi optical engine")
print("  per port 6.4 Tbps / 32 =", 6.4e3 / 32, "Gb/s; line/payload 212.5/200 =", 212.5 / 200)
print("  energy 30 W / 6.4 Tbps =", 30 / 6.4, "pJ/bit; 30 W / 12.8 Tbps =", 30 / 12.8, "pJ/bit")
print("  3.0 pJ/bit at 6.4 Tbps needs", 3.0 * 6.4, "W")
print(f"  1331 - 1311 = {1331 - 1311} nm = {nm_to_ghz(1311) - nm_to_ghz(1331):.1f} GHz")
print(
    "  DR range clearances (delta 0): 1311 ->",
    1311 - 1304.5,
    "and",
    1317.5 - 1311,
    "nm; 1331 upper ->",
    1317.5 - 1331,
    "nm",
)
print("  lanes per laser fiber 32/8 =", 32 / 8, "; fiber reduction 1 - 32/64 =", 1 - 32 / 64)
v_l20, v_plug = 37.5 * 27.6 * 4.55, 108.8 * 22.93 * 15.5
print(f"  volumes {v_l20:.2f} vs {v_plug:.2f} mm3 -> {100 * (1 - v_l20 / v_plug):.2f}% smaller")
print("  18 x 6.4 =", round(18 * 6.4, 6), "Tbps; 6 x 6.4 =", round(6 * 6.4, 6), "Tbps")
print(f"  savings 1 - 5/17 = {100 * (1 - 5 / 17):.2f}%, 1 - 5/20 = {100 * (1 - 5 / 20):.2f}%")

print("§14.3 3D photonic interposer")
print(
    "  256 x 448 Gb/s =",
    256 * 448 / 1000,
    "Tbps; 8 x 56 =",
    8 * 56,
    "; 1024 x 56 x 2 =",
    1024 * 56 * 2 / 1000,
    "Tbps",
)
print("  16 x 2 x 8 =", 16 * 2 * 8, "; 128 x 8 =", 128 * 8, "; 91 x 85 =", 91 * 85, "mm2")
print(
    "  4000 mm2 x 1.4 W/mm2 =",
    4000 * 1.4,
    "W; 1500/7735 =",
    round(1500 / 7735, 4),
    "W/mm2; 1500/4000 =",
    1500 / 4000,
    "W/mm2",
)
io_both, io_dir = 2.3 * 114.688, 2.3 * 114.688 / 2
print(
    f"  I/O at 2.3 pJ/bit: {io_both:.2f} W (Tx + Rx, {100 * io_both / 1500:.1f}% of 1.5 kW),"
    f" {io_dir:.2f} W (per direction)"
)
print("  2048 lambda-channels = 256 x 8 =", 256 * 8)
heater_200 = span_nm(200) / 0.44
print(
    f"  heaters with barrel shifting: 2048 x {heater_200:.4f} mW = {2048 * heater_200 / 1000:.3f} W"
)

print("§14.4 32T CPO chiplet/64T chiplet")
print("  320 x 50 x 2 =", 320 * 50 * 2 / 1000, "Tbps; 320 x 100 x 2 =", 320 * 100 * 2 / 1000)
print(
    "  fibers 32/0.8 =",
    32 / 0.8,
    "; 64/1.6 =",
    64 / 1.6,
    "; 4 x 64 =",
    4 * 64,
    "; 32 Tbps / 40 =",
    32e3 / 40,
    "Gb/s",
)

print("§14.5 16-lambda BiDi link: 16 x 50 =", 16 * 50, "Gb/s; 8 x 50 =", 8 * 50, "each way")
print("  (ring results in s13_ring_wdm.py; minimum TX OMA below)")


def mpi_db(m, er_db, rt_db, rr_db, rc_db, n):
    e = 10 ** (er_db / 10)
    rt, rr, rc = (10 ** (r / 10) for r in (rt_db, rr_db, rc_db))
    s = sqrt(rt * rr) + n * sqrt(rt * rc) + n * sqrt(rr * rc) + n * (n - 1) / 2 * rc
    return -10 * log10(1 - (m - 1) * 4 * s * e / (e - 1))


p_mpi = mpi_db(2, 6, -26, -26, -45, 6)
print(f"  MPI NRZ, ER 6 dB, Rt = Rr = -26 dB, Rc = -45 dB, n = 6: {p_mpi:.4f} dB")
t, r = 10**-0.3, 10**-1.55
for name, x, xr in (("H_fsr18", 0.081869307, 1.082941278), ("H_fsr32", 0.021508348, 0.064485142)):
    pen = -10 * log10(1 - x) + 10 * log10(t / (t - r * xr)) + p_mpi
    print(f"  {name}: minimum TX OMA = -9 + 3 + {pen:.4f} = {-9 + 3 + pen:.4f} dBm")

print("§14.6 ELS family")
print(
    "  8 x 13 mW =",
    8 * 13,
    "mW; 16 x 100 mW =",
    16 * 100 / 1000,
    "W; 32 x 100..110 mW =",
    32 * 100 / 1000,
    "..",
    round(32 * 110 / 1000, 2),
    "W",
)
print("  100 Tbps / 4 =", 100 / 4, "Tbps per module;", end=" ")
print("100/18 =", round(100 / 18, 3), "Tbps per ELSFP")
print(
    "  ELS-DR: 64 x 200 mW =",
    64 * 200 / 1000,
    "W; 256 x 200G =",
    256 * 200 / 1000,
    "Tbps; 256/64 =",
    256 / 64,
    "lanes per laser fiber",
)
print(
    f"  50 mW = {dbm(50):.2f} dBm; 200 mW = {dbm(200):.2f} dBm, {24.5 - dbm(200):.2f} dB under"
    f" 24.5 dBm; 13 mW = {dbm(13):.2f} dBm"
)


def fanout_margin(n, laser_mw=200.0):
    p_avg = dbm(laser_mw) - 0.5 - 1.5 - 10 * log10(n) - 0.0 - 4.0 - 1.5
    er = 10**0.4
    oma = p_avg + 10 * log10(2 * (er - 1) / (er + 1))
    return p_avg, oma, (oma - 3.0 - (-4.3)) - 3.7 - 0.0


for n in (4, 17, 18):
    p_avg, oma, m = fanout_margin(n)
    print(f"  fan-out N = {n}: P_TP2,avg {p_avg:.4f} dBm, OMA {oma:.4f} dBm, M {m:+.4f} dB")
n = 1
while fanout_margin(n + 1)[2] >= -1e-9:
    n += 1
print("  max fan-out", n)

print("§14.7 OCP trays: 204.8/8 =", 204.8 / 8, "; 102.4/4 =", 102.4 / 4, "; /6.4 =", 25.6 / 6.4)
for name, lanes in (("H_dir", 204.8e3 / 200), ("H_agg", 204.8e3 / 2 / 200)):
    print(f"  {name}: {lanes:.0f} lanes per direction -> {lanes / 256:.0f} ELS-DR")
print("  XPU tray under H_dir:", 102.4e3 / 200, "lanes ->", 102.4e3 / 200 / 256, "ELS-DR")

print("§14.8 Pod example")
duplex = 512 * 128 * 2
above = 100 * (duplex / 130000 - 1)
print(
    "  512 x 128 x 2 =",
    duplex,
    f"duplex fibers ({above:.1f}% above 130,000) ->",
    duplex // 2,
    "BiDi",
)
print("  25.6 Tbps per XPU per direction = 128 x 200G:", 128 * 200 / 1000)
hoti = 512 * (32e3 / 200) * 2
print(f"  HOTI26 32 Tbps/XPU -> {hoti:.0f} fibers ({100 * (hoti / 130000 - 1):.0f}% off)")
for miles in (200, 150):
    print(f"  {miles} miles / 65,536 = {miles * 1609.344 / 65536:.4f} m")
print(
    "  65,536/16 =",
    65536 // 16,
    "per mating plane; 4 x 4,096 =",
    4 * 4096,
    f"; 20,000 is {100 * (20000 / 16384 - 1):.0f}% above",
)

print("§14.9 Reference rack OICD-R64")
print(
    "  switch trays 8 x 1 OU + XPU trays 16 x 2 OU + 2 shelves =",
    8 + 32 + 2,
    "OU (H_2U);",
    8 + 16 + 2,
    "OU (H_1U)",
)
print("  links 64 XPUs x 128 lanes =", 64 * 128, "= 8 x 1024; BiDi fibers 8192, duplex", 2 * 8192)
print("  TX lanes 16,384 / 256 =", 16384 // 256, "ELS-DR")
fiber = 4 * 0.4 / 1000
for name, fau in (
    ("FAU 1.5 dB in channel", 1.5),
    ("FAU 1.0 dB in channel", 1.0),
    ("FAU in module", 0.0),
):
    il = 2 * fau + 0.5 + 0.5 + fiber
    m = (2.4 - il - (-4.3)) - 3.7 - 0.0
    print(f"  {name}: IL {il:.4f} dB, M {m:+.4f} dB")
for y in (0.9999, 0.99999):
    print(f"  rack yield y^8192 at y = {y}: {y**8192:.4f}")
y_needed = 0.99 ** (1 / 8192)
lo, hi = 0.0, 10.0
for _ in range(200):
    mid = (lo + hi) / 2
    if 0.5 * erfc(-mid / sqrt(2)) < y_needed:
        lo = mid
    else:
        hi = mid
print(f"  99% rack needs y >= {y_needed:.8f}, z = {lo:.3f} sigma one-sided")
