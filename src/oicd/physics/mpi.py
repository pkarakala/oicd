"""Multipath interference, worst-case bound (model card §12.3, bhatt2016_mpi).

S     = √(Rt·Rr) + n·√(Rt·Rc) + n·√(Rr·Rc) + n(n − 1)/2 · Rc
x     = (m − 1) · 4 · S · E/(E − 1)
Π_MPI = −10·log10(1 − x) dB, invalid input if x ≥ 1

A deterministic upper bound (every interferer coherent, antipodal, at the top PAM level). IEEE
allocates MPI at the 1e-6 cumulative probability point instead (anslow2017_drrefl), so the bound
is conservative.
"""

import math

from pydantic import BaseModel, ConfigDict

_FROZEN = ConfigDict(frozen=True, extra="forbid")


class MpiResult(BaseModel):
    model_config = _FROZEN

    s_linear: float  # summed reflection products S
    x: float
    penalty_db: float
    method: str = "worst-case bound (bhatt2016_mpi); conservative versus the 1e-6 allocation"


def _reflectance(value_db: float, name: str) -> float:
    if not math.isfinite(value_db) or value_db > 0.0:
        raise ValueError(f"{name} must be a finite reflectance <= 0 dB, got {value_db!r}")
    return float(10.0 ** (value_db / 10.0))


def mpi_penalty_db(
    m_levels: int,
    er_db: float,
    rt_db: float,
    rr_db: float,
    rc_db: float,
    n_connectors: int,
) -> MpiResult:
    """Worst-case MPI penalty for PAM-m, ER (dB), reflectances (dB, ≤ 0) and n connectors."""
    if isinstance(m_levels, bool) or not isinstance(m_levels, int) or m_levels < 2:
        raise ValueError(f"m_levels must be an integer >= 2, got {m_levels!r}")
    if isinstance(n_connectors, bool) or not isinstance(n_connectors, int) or n_connectors < 0:
        raise ValueError(f"n_connectors must be an integer >= 0, got {n_connectors!r}")
    if not math.isfinite(er_db) or er_db <= 0.0:
        raise ValueError(f"er_db must be > 0 dB, got {er_db!r}")
    rt, rr, rc = (
        _reflectance(rt_db, "rt_db"),
        _reflectance(rr_db, "rr_db"),
        _reflectance(rc_db, "rc_db"),
    )
    n = n_connectors
    s = math.sqrt(rt * rr) + n * math.sqrt(rt * rc) + n * math.sqrt(rr * rc) + n * (n - 1) / 2 * rc
    e = 10.0 ** (er_db / 10.0)
    x = (m_levels - 1) * 4.0 * s * e / (e - 1.0)
    if x >= 1.0:
        raise ValueError(f"MPI bound diverges: x = {x} >= 1 (reflections too strong)")
    return MpiResult(s_linear=s, x=x, penalty_db=-10.0 * math.log10(1.0 - x))
