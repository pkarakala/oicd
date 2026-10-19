"""Hand calculations for model card §9 (multi-lane tray). Standard library only."""

from fractions import Fraction as F


def lane_margin(patch_db):
    losses = [F("1.5"), F("0.0004"), F(patch_db), F("0.0004"), F("1.5")]
    return (F(0) - sum(losses, F(0)) - F(-6)) - F("1.5")


lanes = [lane_margin("1.0") for _ in range(8)]
lanes[5] = lane_margin("2.0")  # lane 5 (index 5, the sixth lane)
m = min(lanes)
print("lane margins:", [f"{float(v):+.4f}" for v in lanes])
print(
    f"tray margin {float(m):+.4f} dB, deciding lane {lanes.index(m)},",
    "EXCLUDED" if m < 0 else "NOT_EXCLUDED",
)
