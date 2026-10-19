"""Worst-case OMA power budget, TP2 to TP3 (model card §3).

P_TP3,OMA = P_TP2,OMA,min − Σ L_i,max
M_net     = (P_TP3,OMA − S_RX,OMA,max) − Σ Π_j − R
PASS iff M_net ≥ −ε

P_TP2 is the fixed launch_oma_min or, when the transmitter has an upstream chain, the TP2
derived from the laser (model card §10).
"""

from oicd.checks import CheckResult, Status
from oicd.registry import EPSILON_DB, ConstraintId
from oicd.schema import Link
from oicd.units import DB, PowerKind, UnitMismatchError
from oicd.upstream import tp2_launch


def check_power_budget(link: Link) -> CheckResult:
    launch = tp2_launch(link.tx)
    sensitivity = link.rx.sensitivity_oma_max.value
    # The schema already enforces OMA; this guard keeps the check correct on its own.
    if launch.kind is not PowerKind.OMA or sensitivity.kind is not PowerKind.OMA:
        raise UnitMismatchError(
            f"power budget is OMA only, got TX {launch.kind.value} and RX {sensitivity.kind.value}"
        )

    total_loss = sum((e.loss_max.value for e in link.channel), start=DB(0.0))
    penalties = sum((p.value.value for p in link.penalties), start=DB(0.0))
    reserve = link.reserve.value

    p_tp3 = launch - total_loss
    margin = (p_tp3 - sensitivity) - penalties - reserve
    passed = margin.value >= -EPSILON_DB

    evidence: dict[str, float | str] = {
        "total_loss_db": total_loss.value,
        "p_tp3_dbm": p_tp3.power_dbm.value,
        "sensitivity_dbm": sensitivity.power_dbm.value,
        "penalties_db": penalties.value,
        "reserve_db": reserve.value,
        "margin_db": margin.value,
        "epsilon_db": EPSILON_DB,
        "penalty_names": ", ".join(p.name for p in link.penalties),
        "tp2_source": "fixed" if link.tx.upstream is None else "upstream chain",
    }
    named = ", ".join(f"{p.name} {p.value.value.value} dB" for p in link.penalties) or "none"
    return CheckResult(
        constraint=ConstraintId.OPTICAL_POWER_BUDGET,
        status=Status.PASS if passed else Status.FAIL,
        evidence=evidence,
        message=(
            f"M_net = {margin.value} dB ({'>=' if passed else '<'} -{EPSILON_DB} dB); "
            f"P_TP3 = {p_tp3.power_dbm.value} dBm OMA after {total_loss.value} dB loss; "
            f"penalties: {named}; reserve {reserve.value} dB"
        ),
    )
