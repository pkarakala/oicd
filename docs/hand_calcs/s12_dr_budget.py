"""Hand calculations for model card §12: the draft IEEE P802.3dj 200GBASE-DR1 budget, the
Table 180-12 lookup, the MPI worst-case bound and reflection crosstalk. Standard library only.
All 802.3dj values are PROPOSED_STANDARD (draft D3.x, not approved)."""

from fractions import Fraction as F
from math import log10, sqrt

print("§12.1 DR budget")
tdecq = F("3.4")
oma_min = F(-1) + tdecq  # OMAouter min = -1 + max(TECQ, TDECQ), at TDECQ max
s_ref = F("-4.3")  # receiver sensitivity line -4.3 + TECQ at TECQ = 0
il, mpi, dgd, reserve = F(3), F("0.1"), F("0.2"), F(0)
print("  TX OMAouter min at max TDECQ =", float(oma_min), "dBm")
print("  power budget                 =", float(oma_min - s_ref), "dB")
print("  allocation for penalties     =", float(oma_min - s_ref - il), "dB")
print("  named penalties sum          =", float(tdecq + mpi + dgd), "dB")
print("  exact M_net                  =", (oma_min - il - s_ref) - (tdecq + mpi + dgd) - reserve)
# Float, in the engine's order: P_TP3 = launch - (0 + IL);
# M = ((P_TP3 - S) - (((0 + 3.4) + 0.1) + 0.2)) - R
p_tp3 = 2.4 - (0.0 + 3.0)
m_float = ((p_tp3 - (-4.3)) - (((0.0 + 3.4) + 0.1) + 0.2)) - 0.0
print("  float M_net                  =", m_float)

print("§12.2 Table 180-12 cases (row = count in (-45, -35] dB, column = count in (-55, -45] dB)")
table = [
    [3, 3, 3, 3, 3, 3, 2.9, 2.9, 2.9],
    [3, 3, 3, 2.9, 2.9, 2.9, 2.9, 2.8, 2.8],
    [2.9, 2.9, 2.9, 2.8, 2.8, 2.8, 2.7, 2.7, 2.7],
    [2.8, 2.8, 2.7, 2.7, 2.7, 2.6, 2.6, 2.6, 2.6],
    [2.7, 2.6, 2.6, 2.6, 2.5, 2.5, 2.5, 2.5, None],
    [2.5, 2.5, 2.5, None, None, None, None, None, None],
    [None] * 9,
]
for row, col in [(0, 0), (0, 6), (2, 3), (4, 4), (5, 0), (4, 8), (6, 0)]:
    v = table[row][col]
    print(f"  ({row}, {col}) ->", "not supported" if v is None else f"{v} dB")

print("§12.3 MPI worst-case bound (bhatt2016_mpi): PAM4 m = 4, ER 6 dB, Rt -20, Rr -26, Rc -35 dB")


def mpi_db(m, er_db, rt_db, rr_db, rc_db, n):
    e = 10 ** (er_db / 10)
    rt, rr, rc = (10 ** (r / 10) for r in (rt_db, rr_db, rc_db))
    s = sqrt(rt * rr) + n * sqrt(rt * rc) + n * sqrt(rr * rc) + n * (n - 1) / 2 * rc
    x = (m - 1) * 4 * s * e / (e - 1)
    return -10 * log10(1 - x)


for n in (2, 4, 6):
    print(f"  n = {n}: {mpi_db(4, 6, -20, -26, -35, n):.4f} dB")

print("§12.4 reflection crosstalk (bhatt2001_bidixtalk)")


def xtalk_db(il_db, rl_db, isolation_db=0.0):
    t = 10 ** (-il_db / 10)
    r = 10 ** (-(rl_db + isolation_db) / 10)
    return 10 * log10(t / (t - r))


print(f"  IL 7, RL 12 (published example)       : {xtalk_db(7, 12):.4f} dB")
print(f"  IL 3, RL 15.5, I 0 (two-wavelength)   : {xtalk_db(3, 15.5, 0):.4f} dB")
print(f"  IL 3, RL 15.5, I 25 (two-wavelength)  : {xtalk_db(3, 15.5, 25):.6f} dB")
print("  source rule: return loss >= IL + 5 dB; IL 3 -> RL >= 8 dB")
