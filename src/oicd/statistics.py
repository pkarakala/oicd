"""Statistical budget and yield (model card §11). Statistical, assumption-dependent.

Loss elements with a LossDistribution are independent normals N(μ, σ²) (SYNTHETIC assumption);
the others stay at loss_max. yield = Φ(M_mean / σ_total), σ_total = sqrt(Σ σ_i²). A seeded
Monte Carlo evaluates M_net per sample with the §3 expression and must reproduce it. Nothing
here changes the worst-case verdict, which evaluate() decides with every loss at loss_max.
"""

import math
from collections.abc import Sequence
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict

from oicd.provenance import SourceClass
from oicd.registry import EPSILON_DB
from oicd.report import evaluate
from oicd.schema import Link
from oicd.upstream import tp2_launch

_FROZEN = ConfigDict(frozen=True, extra="forbid")

LABEL: Literal["statistical, assumption-dependent"] = "statistical, assumption-dependent"
MAX_SAMPLES = 1_000_000
MAX_BINS = 400

Verdict = Literal["NOT_EXCLUDED", "EXCLUDED"]


class DistributedLoss(BaseModel):
    model_config = _FROZEN

    path: str
    name: str
    mean_db: float
    sigma_db: float
    source_class: SourceClass


class AnalyticYield(BaseModel):
    model_config = _FROZEN

    label: Literal["statistical, assumption-dependent"] = LABEL
    worst_case_verdict: Verdict
    worst_case_margin_db: float
    m_mean_db: float
    sigma_total_db: float
    z: float | None  # M_mean / σ_total; None when σ_total = 0
    yield_fraction: float
    margin_at_3sigma_db: float
    distributed: tuple[DistributedLoss, ...]


class Histogram(BaseModel):
    """M_net samples binned over M_mean ± 5σ_total; samples outside are counted apart."""

    model_config = _FROZEN

    edges_db: tuple[float, ...]
    counts: tuple[int, ...]
    below: int
    above: int


class MonteCarloYield(BaseModel):
    model_config = _FROZEN

    label: Literal["statistical, assumption-dependent"] = LABEL
    n_samples: int
    seed: int
    yield_fraction: float
    standard_error: float
    sample_mean_db: float
    sample_std_db: float
    histogram: Histogram


def normal_cdf(z: float) -> float:
    """Φ(z) = ½·erfc(−z/√2), accurate in both tails."""
    return 0.5 * math.erfc(-z / math.sqrt(2.0))


def _distributed(link: Link) -> tuple[DistributedLoss, ...]:
    return tuple(
        DistributedLoss(
            path=f"channel[{i}].loss_distribution",
            name=e.name,
            mean_db=e.loss_distribution.mean.value.value,
            sigma_db=e.loss_distribution.sigma.value.value,
            source_class=e.loss_distribution.sigma.provenance.source_class,
        )
        for i, e in enumerate(link.channel)
        if e.loss_distribution is not None
    )


def _margin(link: Link, losses: Sequence[float | np.ndarray]) -> float | np.ndarray:
    """M_net with the given per-element losses, in the §3 order."""
    total: float | np.ndarray = 0.0
    for loss in losses:
        total = total + loss
    penalties = 0.0
    for p in link.penalties:
        penalties = penalties + p.value.value.value
    p_tp3 = tp2_launch(link.tx).power_dbm.value - total
    s_rx = link.rx.sensitivity_oma_max.value.power_dbm.value
    return ((p_tp3 - s_rx) - penalties) - link.reserve.value.value


def analytic_yield(link: Link) -> AnalyticYield:
    report = evaluate(link)
    means = [
        e.loss_distribution.mean.value.value if e.loss_distribution else e.loss_max.value.value
        for e in link.channel
    ]
    m_mean = float(_margin(link, means))
    sigma = math.sqrt(
        sum(e.loss_distribution.sigma.value.value**2 for e in link.channel if e.loss_distribution)
    )
    if sigma > 0.0:
        z: float | None = m_mean / sigma
        fraction = normal_cdf(m_mean / sigma)
    else:
        z = None
        fraction = 1.0 if m_mean >= -EPSILON_DB else 0.0
    return AnalyticYield(
        worst_case_verdict=report.verdict,
        worst_case_margin_db=report.margin_db,
        m_mean_db=m_mean,
        sigma_total_db=sigma,
        z=z,
        yield_fraction=fraction,
        margin_at_3sigma_db=m_mean - 3.0 * sigma,
        distributed=_distributed(link),
    )


def monte_carlo_yield(
    link: Link, n_samples: int = 100_000, seed: int = 0, bins: int = 60
) -> MonteCarloYield:
    """Seeded Monte Carlo of M_net (§11); same inputs and seed give the same result bit for bit."""
    if not 1 <= n_samples <= MAX_SAMPLES:
        raise ValueError(f"n_samples must be 1 to {MAX_SAMPLES}, got {n_samples}")
    if not 1 <= bins <= MAX_BINS:
        raise ValueError(f"bins must be 1 to {MAX_BINS}, got {bins}")
    if seed < 0:
        raise ValueError(f"seed must be >= 0, got {seed}")
    rng = np.random.default_rng(seed)
    losses: list[float | np.ndarray] = []
    for element in link.channel:  # draws in channel order, so the stream is reproducible
        dist = element.loss_distribution
        if dist is None:
            losses.append(element.loss_max.value.value)
        else:
            losses.append(rng.normal(dist.mean.value.value, dist.sigma.value.value, n_samples))
    margins = np.broadcast_to(np.asarray(_margin(link, losses), dtype=float), (n_samples,))
    fraction = float(np.count_nonzero(margins >= -EPSILON_DB)) / n_samples
    analytic = analytic_yield(link)
    half_width = 5.0 * analytic.sigma_total_db if analytic.sigma_total_db > 0 else 1.0
    counts, edges = np.histogram(
        margins, bins=bins, range=(analytic.m_mean_db - half_width, analytic.m_mean_db + half_width)
    )
    return MonteCarloYield(
        n_samples=n_samples,
        seed=seed,
        yield_fraction=fraction,
        standard_error=math.sqrt(fraction * (1.0 - fraction) / n_samples),
        sample_mean_db=float(np.mean(margins)),
        sample_std_db=float(np.std(margins)),
        histogram=Histogram(
            edges_db=tuple(float(v) for v in edges),
            counts=tuple(int(c) for c in counts),
            below=int(np.count_nonzero(margins < edges[0])),
            above=int(np.count_nonzero(margins > edges[-1])),
        ),
    )
