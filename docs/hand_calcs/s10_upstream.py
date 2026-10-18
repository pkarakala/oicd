"""Hand calculations for model card §10 (upstream chain, TP2 derived). Standard library only."""

from math import log10


def tp2(n, laser_dbm=20.0, fiber=0.5, couple=1.5, excess=0.0, mod=4.0, out=1.5, er_db=4.0):
    p_avg = laser_dbm - fiber - couple - 10 * log10(n) - excess - mod - out
    er = 10 ** (er_db / 10)
    oma = p_avg + 10 * log10(2 * (er - 1) / (er + 1))
    return p_avg, oma


def margin(oma, channel=4.0008, s_rx=-6.0, reserve=1.5):
    return (oma - channel - s_rx) - reserve


for n in (16, 17, 18):
    p_avg, oma = tp2(n)
    m = margin(oma)
    print(
        f"N = {n}: P_TP2,avg {p_avg:+.4f} dBm, P_TP2,OMA {oma:+.4f} dBm, M {m:+.4f} dB",
        "NOT_EXCLUDED" if m >= -1e-9 else "EXCLUDED",
    )
n = 1
while margin(tp2(n + 1)[1]) >= -1e-9:
    n += 1
print("max fan-out:", n)
