"""Hand calculations for model card §4 (worked example) and §5 (T01 to T16).

Standard library only; never imports oicd. Exact arithmetic with Fraction where the card says
"exact", floats only to show what a float sum gives.
"""

from fractions import Fraction as F
from math import log10


def margin(launch, losses, sensitivity, penalties, reserve):
    return (launch - sum(losses, F(0)) - sensitivity) - sum(penalties, F(0)) - reserve


print("§4 worked example")
losses = [F("1.5"), F("0.0004"), F("1.0"), F("0.0004"), F("1.5")]
print("  sum L      =", float(sum(losses)), "dB")
print("  P_TP3      =", float(-sum(losses)), "dBm OMA")
print("  M_net      =", float(margin(F(0), losses, F(-6), [], F("1.5"))), "dB")

print("§5 power budget cases (T01 inputs unless stated)")
for tid, ls, pens, r in [
    ("T01", ["4.0"], [], "1.5"),
    ("T02", ["5.0"], [], "1.5"),
    ("T03", ["4.5"], [], "1.5"),
    ("T04", ["0.3", "1.3", "3.3"], [], "1.1"),
    ("T05", ["4.0", "0.5"], [], "1.5"),
    ("T06", ["4.0"], ["1.0"], "1.5"),
    ("T16", ["0.1", "0", "1.0", "0", "0.2"], [], "4.7"),
]:
    m = margin(F(0), [F(x) for x in ls], F(-6), [F(x) for x in pens], F(r))
    print(f"  {tid}: exact M = {m} dB")

float_t04 = (0.0 - (0.0 + 0.3 + 1.3 + 3.3) - (-6.0)) - 0.0 - 1.1
print("  T04 float M =", float_t04)

er = 10 ** (4 / 10)
print(
    "T08 OMA at P_avg 0 dBm, ER 4 dB =", round(10 * log10(2 * 1.0 * (er - 1) / (er + 1)), 5), "dBm"
)
print("T09 clearances:", (1310 - 2) - 1300, 1320 - (1310 + 2), "nm")
print("T10 upper edge and clearance:", 1318 + 3, 1320 - (1318 + 3), "nm")
