"""Hand calculations for model card §15 (photonic processor, ahmed2025_nature).

Standard library only; never imports oicd.
"""

from math import ceil, frexp, log2

print("§15.2 derived values")
macs = 4 * 128 * 128
print(f"  MAC per cycle 4 x 128 x 128 = {macs}")
print(f"  x 2 ops x 500 MHz = {macs * 2 * 500e6 / 1e12:.3f} TOPS")
print(f"  x 2 ops x 2 GHz = {macs * 2 * 2e9 / 1e12:.3f} TOPS")
power = 4 * 3.2 + 65
print(f"  4 x 3.2 W + 65 W = {power:.1f} W; lasers 8 x 1.25 W = {8 * 1.25:.0f} W")
ops = macs * 2 * 500e6 / 1e12
print(f"  {ops:.3f} TOPS / 78 W = {ops / 78:.4f} TOPS/W; / 88 W = {ops / 88:.4f} TOPS/W")
ptc_mm2, dci_mm2 = 14.00 * 24.96, 31.4 * 25.0
print(f"  PTC 14.00 x 24.96 = {ptc_mm2:.2f} mm2; control die 31.4 x 25.0 = {dci_mm2:.0f} mm2")
print(f"  lasers 8 x 200 mW = {8 * 200 / 1000:.1f} W optical")


def output_word_bits(wb, xb, n):
    return wb + xb + log2(n) - 1


word_n = output_word_bits(7, 10, 128)
print(f"  output word, range n = 128: 7 + 10 + log2(128) - 1 = {word_n:.0f} bits")
print(f"  output word, range 1: 7 + 10 + log2(1) - 1 = {output_word_bits(7, 10, 1):.0f} bits")

print("§15.3 ABFP hand cases (round half to even)")


def q(x, b, s):
    levels = 2 ** (b - 1) - 1
    codes = [max(-levels, min(levels, round(v / s * levels))) for v in x]
    return codes, [c / levels * s for c in codes]


x = [0.3, -1.2, 0.05, 0.9]
for label, s in (("exact scale 1.2", 1.2), ("bfloat16 scale", None)):
    if s is None:
        m, e = frexp(1.2)
        step = 2.0 ** (e - 8)
        s = ceil(1.2 / step) * step
        print(f"  bfloat16 rounded up: 1.2 -> {s}")
    codes, deq = q(x, 7, s)
    err = max(abs(a - b) for a, b in zip(x, deq, strict=True))
    rounded = [round(v, 6) for v in deq]
    print(f"  {label}: codes {codes}, dequantized {rounded}, max abs error {err:.6f}")

print("§15.3 ADC noise from ENOB 9.8: SNR = 6.02 x 9.8 + 1.76 dB")
snr = 6.02 * 9.8 + 1.76
print(f"  SNR {snr:.3f} dB; noise rms / full scale = {1 / (2**0.5 * 10 ** (snr / 20)):.6e}")

print("§15.5 per-weight-cell optical power (stretch)")
cells = 4 * 128 * 128
for name, extra_db in (("H_lasers_dedicated", 0.0), ("H_lasers_shared", 0.5)):
    loss = 1.56 + 1.1 + 1.35 + extra_db
    per_cell_uw = 1600.0 * 10 ** (-loss / 10) / cells * 1000
    print(f"  {name}: 1.6 W x 10^(-{loss:.2f}/10) / {cells} = {per_cell_uw:.4f} uW per cell")
print(f"  before any loss: {1600.0 / cells * 1000:.4f} uW per cell")
