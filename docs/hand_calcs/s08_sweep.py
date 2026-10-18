"""Hand calculations for model card §8 (design-space sweep). Standard library only."""

from fractions import Fraction as F


def margin(launch, losses, sensitivity=F(-6), penalties=(), reserve=F("1.5")):
    return (launch - sum(losses, F(0)) - sensitivity) - sum(penalties, F(0)) - reserve


def worked(patch_db, tx_oma_dbm):
    # §4 channel in §2 order; the patch connector is the third element (channel[2]).
    losses = [F("1.5"), F("0.0004"), F(patch_db), F("0.0004"), F("1.5")]
    return margin(F(tx_oma_dbm), losses)


for x, y in [("1.0", "0"), ("2.0", "0"), ("0", "1")]:
    print(f"(patch {x} dB, TX OMA {y} dBm) -> M = {float(worked(x, y)):+.4f} dB")
print("slope dM/dL_patch =", float(worked("1.5", "0") - worked("0.5", "0")), "dB per dB")
print("slope dM/dP_TP2   =", float(worked("1.0", "1") - worked("1.0", "0")), "dB per dB")
