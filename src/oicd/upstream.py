"""Upstream chain from the laser to TP2 (model card §10, Milestone 2).

P_TP2,avg = P_laser,avg − L_laser_fiber − L_couple − 10·log10(N) − L_excess − L_mod − L_out
P_TP2,OMA = P_TP2,avg + 10·log10(2(ER − 1)/(ER + 1))

The derived TP2 replaces the fixed launch_oma_min when a transmitter carries a chain. Pure
functions; the same chain gives the same TP2 bit for bit.
"""

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict

from oicd.schema import Link, Transmitter, UpstreamChain
from oicd.units import DB, OpticalPower, PowerKind, oma_offset_db

_FROZEN = ConfigDict(frozen=True, extra="forbid")

# max_fanout searches N = 1 … MAX_FANOUT_SEARCH. A search limit, not a physical parameter.
MAX_FANOUT_SEARCH = 65536


class UpstreamStep(BaseModel):
    """Power after one upstream element. Average power, except the final OMA step at TP2."""

    model_config = _FROZEN

    name: str
    input_path: str | None
    loss_db: float | None  # None for the laser itself and the OMA conversion
    power_dbm: float
    kind: Literal["average", "oma"]


def split_loss_db(n: int) -> DB:
    """Ideal 1:N split, 10·log10(N)."""
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError(f"split N must be an integer >= 1, got {n!r}")
    return DB(10.0 * math.log10(n))


def derive_tp2(chain: UpstreamChain) -> tuple[OpticalPower, tuple[UpstreamStep, ...]]:
    """TP2 OMA from the chain, with the itemized average-power trace (model card §10)."""
    power = chain.laser_power_avg.value
    steps = [
        UpstreamStep(
            name="laser output (average)",
            input_path="tx.upstream.laser_power_avg",
            loss_db=None,
            power_dbm=power.power_dbm.value,
            kind="average",
        )
    ]
    losses: tuple[tuple[str, str, DB], ...] = (
        ("laser fiber and connector", "laser_fiber_loss", chain.laser_fiber_loss.value),
        ("fiber-to-PIC coupling", "coupling_loss", chain.coupling_loss.value),
        (f"1:{chain.split_n.value} split", "split_n", split_loss_db(chain.split_n.value)),
        ("split excess", "excess_loss", chain.excess_loss.value),
        ("modulator insertion loss", "modulator_il", chain.modulator_il.value),
        ("output coupler", "output_coupler_loss", chain.output_coupler_loss.value),
    )
    for name, field, loss in losses:
        power = power - loss
        steps.append(
            UpstreamStep(
                name=name,
                input_path=f"tx.upstream.{field}",
                loss_db=loss.value,
                power_dbm=power.power_dbm.value,
                kind="average",
            )
        )
    oma = OpticalPower(power.power_dbm + oma_offset_db(chain.extinction_ratio.value), PowerKind.OMA)
    steps.append(
        UpstreamStep(
            name="TP2 OMA (extinction ratio)",
            input_path="tx.upstream.extinction_ratio",
            loss_db=None,
            power_dbm=oma.power_dbm.value,
            kind="oma",
        )
    )
    return oma, tuple(steps)


def tp2_launch(tx: Transmitter) -> OpticalPower:
    """The TP2 OMA a transmitter launches: the fixed value, or the one derived from its chain."""
    if tx.launch_oma_min is not None:
        return tx.launch_oma_min.value
    if tx.upstream is None:  # the schema forbids this; kept so the function stands alone
        raise ValueError("transmitter has neither launch_oma_min nor upstream")
    return derive_tp2(tx.upstream)[0]


def with_split(link: Link, n: int) -> Link:
    """The same link with the chain's split set to N (provenance kept)."""
    tx = link.tx
    if tx.upstream is None:
        raise ValueError("link has no upstream chain")
    split = tx.upstream.split_n.model_copy(update={"value": n})
    upstream = tx.upstream.model_copy(update={"split_n": split})
    return link.model_copy(update={"tx": tx.model_copy(update={"upstream": upstream})})


def max_fanout(link: Link) -> int:
    """Largest N in 1 … MAX_FANOUT_SEARCH with the link NOT_EXCLUDED, by search (§10).

    M_net falls monotonically with N, so an exponential search brackets the boundary and a
    binary search finds it. Returns 0 if N = 1 is already excluded, MAX_FANOUT_SEARCH if the
    link still passes there.
    """
    # Imported here because the power-budget check imports tp2_launch from this module.
    from oicd.checks import Status
    from oicd.checks.electrical import check_electrical
    from oicd.checks.power_budget import check_power_budget
    from oicd.checks.wavelength import check_wavelength

    # N changes only TP2, so the electrical and wavelength checks are evaluated once.
    if Status.FAIL in (check_electrical(link).status, check_wavelength(link).status):
        return 0

    def passes(n: int) -> bool:
        return check_power_budget(with_split(link, n)).status is Status.PASS

    if not passes(1):
        return 0
    good, bad = 1, 2
    while bad <= MAX_FANOUT_SEARCH and passes(bad):
        good, bad = bad, bad * 2
    if bad > MAX_FANOUT_SEARCH:
        if passes(MAX_FANOUT_SEARCH):
            return MAX_FANOUT_SEARCH
        bad = MAX_FANOUT_SEARCH
    while bad - good > 1:
        mid = (good + bad) // 2
        if passes(mid):
            good = mid
        else:
            bad = mid
    return good
