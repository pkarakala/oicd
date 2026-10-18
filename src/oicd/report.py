"""Feasibility report: runs every check on a Link and records inputs, trace and verdict.

The report is the only interface the API and the web explorer read. Every number in it is
computed here (or by the checks); consumers display it and never recompute dB.
"""

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict

from oicd.checks import CheckResult, Status
from oicd.checks.electrical import check_electrical
from oicd.checks.power_budget import check_power_budget
from oicd.checks.wavelength import check_wavelength
from oicd.provenance import Provenance, SourceClass
from oicd.registry import EPSILON_DB, NOT_EVALUATED, ConstraintId
from oicd.schema import Link, UpstreamChain
from oicd.units import DB, DBm, oma_offset_db
from oicd.upstream import UpstreamStep, derive_tp2, max_fanout, tp2_launch

_FROZEN = ConfigDict(frozen=True, extra="forbid")

# One line per constraint the model does not decide (model card §1).
NOT_EVALUATED_REASONS: dict[ConstraintId, str] = {
    ConstraintId.BER: "BER is not predicted; the budget assumes the receiver meets its FEC "
    "threshold at the stated sensitivity.",
    ConstraintId.TDECQ: "Eye quality (TDECQ) is not modeled; it enters only as a named penalty "
    "if one is given.",
    ConstraintId.DISPERSION: "Chromatic dispersion is not modeled.",
    ConstraintId.REFLECTIONS_MPI: "Reflections and multipath interference are not modeled.",
    ConstraintId.THERMAL: "Thermal behavior (wavelength drift, power over temperature) is not "
    "modeled.",
    ConstraintId.RELIABILITY: "Reliability and aging are not modeled.",
}


class InputRecord(BaseModel):
    """One physical input to the evaluation, with its provenance."""

    model_config = _FROZEN

    path: str
    name: str
    value: float | int | str
    unit: str
    source_class: SourceClass
    citation_key: str | None
    rationale: str


class TracePoint(BaseModel):
    """OMA at TP2, after each channel element in order, and at TP3.

    loss_db and loss_fraction (share of the total channel loss) are set for loss elements and
    are None at the reference planes. headroom_db = power_dbm − threshold_dbm (model card §3),
    computed in the same order as M_net, so the TP3 value equals margin_db exactly.
    above_threshold = headroom_db ≥ −ε, the verdict's pass rule; displays use only this flag to
    decide above or below threshold.
    """

    model_config = _FROZEN

    kind: Literal["reference_plane", "loss_element"]
    name: str
    channel_index: int | None
    input_path: str | None
    power_dbm: float
    loss_db: float | None
    loss_fraction: float | None
    headroom_db: float
    above_threshold: bool


class UpstreamSection(BaseModel):
    """TP2 derived from the laser (model card §10). The derived TP2 is INFERENCE: it is computed
    from the chain inputs, whose own provenance is listed in the report's inputs."""

    model_config = _FROZEN

    chain_name: str
    split_n: int
    steps: tuple[UpstreamStep, ...]
    p_tp2_avg_dbm: float
    p_tp2_oma_dbm: float
    oma_offset_db: float
    max_fanout: int
    tp2_source_class: SourceClass
    derivation: str


class FeasibilityReport(BaseModel):
    model_config = _FROZEN

    link_name: str
    verdict: Literal["NOT_EXCLUDED", "EXCLUDED"]
    margin_db: float
    threshold_dbm: float
    results: tuple[CheckResult, ...]
    not_evaluated: tuple[CheckResult, ...]
    inputs: tuple[InputRecord, ...]
    power_trace: tuple[TracePoint, ...]
    upstream: UpstreamSection | None = None

    def to_json(self) -> str:
        """Deterministic JSON: sorted keys, compact separators, Python's shortest round-trip
        float repr. NaN and infinity cannot occur (the schema rejects them) and would raise."""
        return json.dumps(
            self.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )


def _record(
    path: str, name: str, value: float | int | str, unit: str, provenance: Provenance
) -> InputRecord:
    return InputRecord(
        path=path,
        name=name,
        value=value,
        unit=unit,
        source_class=provenance.source_class,
        citation_key=provenance.citation_key,
        rationale=provenance.rationale,
    )


def collect_inputs(link: Link) -> tuple[InputRecord, ...]:
    records: list[InputRecord] = []
    for side, part in (("tx", link.tx), ("rx", link.rx)):
        el = part.electrical
        for field, unit in (
            ("modulation", ""),
            ("symbol_rate_gbd", "GBd"),
            ("lanes", "lanes"),
            ("fec", ""),
        ):
            value = getattr(el, field)
            value = str(value) if isinstance(value, str) else value
            records.append(
                _record(f"{side}.electrical.{field}", part.name, value, unit, el.provenance)
            )
    tx, rx = link.tx, link.rx
    records += [
        _record(
            "tx.center_wavelength_nm",
            tx.name,
            tx.center_wavelength_nm.value,
            "nm",
            tx.center_wavelength_nm.provenance,
        ),
        _record(
            "tx.wavelength_tolerance_nm",
            tx.name,
            tx.wavelength_tolerance_nm.value,
            "nm",
            tx.wavelength_tolerance_nm.provenance,
        ),
    ]
    if tx.launch_oma_min is not None:
        records.append(
            _record(
                "tx.launch_oma_min",
                tx.name,
                tx.launch_oma_min.value.power_dbm.value,
                f"dBm {tx.launch_oma_min.value.kind.value.upper()}",
                tx.launch_oma_min.provenance,
            )
        )
    if tx.upstream is not None:
        records += _upstream_records(tx.upstream)
    records += [
        _record(
            "rx.passband_min_nm",
            rx.name,
            rx.passband_min_nm.value,
            "nm",
            rx.passband_min_nm.provenance,
        ),
        _record(
            "rx.passband_max_nm",
            rx.name,
            rx.passband_max_nm.value,
            "nm",
            rx.passband_max_nm.provenance,
        ),
        _record(
            "rx.sensitivity_oma_max",
            rx.name,
            rx.sensitivity_oma_max.value.power_dbm.value,
            f"dBm {rx.sensitivity_oma_max.value.kind.value.upper()}",
            rx.sensitivity_oma_max.provenance,
        ),
    ]
    for i, element in enumerate(link.channel):
        records.append(
            _record(
                f"channel[{i}].loss_max",
                element.name,
                element.loss_max.value.value,
                "dB",
                element.loss_max.provenance,
            )
        )
    for i, penalty in enumerate(link.penalties):
        records.append(
            _record(
                f"penalties[{i}].value",
                penalty.name,
                penalty.value.value.value,
                "dB",
                penalty.value.provenance,
            )
        )
    records.append(
        _record("reserve", "reserve", link.reserve.value.value, "dB", link.reserve.provenance)
    )
    return tuple(records)


def _upstream_records(chain: UpstreamChain) -> list[InputRecord]:
    laser = chain.laser_power_avg
    records = [
        _record(
            "tx.upstream.laser_power_avg",
            chain.name,
            laser.value.power_dbm.value,
            f"dBm {laser.value.kind.value.upper()}",
            laser.provenance,
        )
    ]
    for field in ("laser_fiber_loss", "coupling_loss"):
        q = getattr(chain, field)
        records.append(
            _record(f"tx.upstream.{field}", chain.name, q.value.value, "dB", q.provenance)
        )
    records.append(
        _record(
            "tx.upstream.split_n",
            chain.name,
            chain.split_n.value,
            "outputs",
            chain.split_n.provenance,
        )
    )
    for field in ("excess_loss", "modulator_il", "output_coupler_loss", "extinction_ratio"):
        q = getattr(chain, field)
        records.append(
            _record(f"tx.upstream.{field}", chain.name, q.value.value, "dB", q.provenance)
        )
    return records


def upstream_section(link: Link) -> UpstreamSection | None:
    chain = link.tx.upstream
    if chain is None:
        return None
    oma, steps = derive_tp2(chain)
    avg = steps[-2].power_dbm
    offset = oma_offset_db(chain.extinction_ratio.value).value
    return UpstreamSection(
        chain_name=chain.name,
        split_n=chain.split_n.value,
        steps=steps,
        p_tp2_avg_dbm=avg,
        p_tp2_oma_dbm=oma.power_dbm.value,
        oma_offset_db=offset,
        max_fanout=max_fanout(link),
        tp2_source_class=SourceClass.INFERENCE,
        derivation=(
            f"P_TP2,avg = {chain.laser_power_avg.value.power_dbm.value} dBm − "
            f"{chain.laser_fiber_loss.value.value} − {chain.coupling_loss.value.value} − "
            f"10·log10({chain.split_n.value}) − {chain.excess_loss.value.value} − "
            f"{chain.modulator_il.value.value} − {chain.output_coupler_loss.value.value} dB "
            f"= {avg} dBm; P_TP2,OMA = P_TP2,avg + 10·log10(2(ER−1)/(ER+1)) at ER "
            f"{chain.extinction_ratio.value.value} dB = {oma.power_dbm.value} dBm (model card §10)"
        ),
    )


def threshold(link: Link) -> DBm:
    """Required OMA at TP3: S_RX,OMA,max + Σ Π_j + R (model card §3 rearranged)."""
    penalties = sum((p.value.value for p in link.penalties), start=DB(0.0))
    return link.rx.sensitivity_oma_max.value.power_dbm + penalties + link.reserve.value


def power_trace(link: Link) -> tuple[TracePoint, ...]:
    """OMA at TP2, after each loss element, and at TP3.

    Losses are accumulated in channel order with the same start and order as the power-budget
    check, so the TP3 point equals the check's p_tp3_dbm exactly. Headroom is evaluated as
    (P − S_RX) − ΣΠ − R, the order of M_net, so headroom and above_threshold at TP3 equal the
    check's margin_db and status bit for bit (model card §3).
    """
    launch = tp2_launch(link.tx).power_dbm
    sensitivity = link.rx.sensitivity_oma_max.value.power_dbm
    penalties = sum((p.value.value for p in link.penalties), start=DB(0.0))
    reserve = link.reserve.value
    total_loss = sum((e.loss_max.value for e in link.channel), start=DB(0.0))

    def point(
        kind: Literal["reference_plane", "loss_element"],
        name: str,
        power: DBm,
        index: int | None = None,
        loss: DB | None = None,
    ) -> TracePoint:
        fraction = None
        if loss is not None:
            fraction = loss.value / total_loss.value if total_loss.value > 0.0 else 0.0
        headroom = ((power - sensitivity) - penalties) - reserve
        return TracePoint(
            kind=kind,
            name=name,
            channel_index=index,
            input_path=None if index is None else f"channel[{index}].loss_max",
            power_dbm=power.value,
            loss_db=None if loss is None else loss.value,
            loss_fraction=fraction,
            headroom_db=headroom.value,
            above_threshold=headroom.value >= -EPSILON_DB,
        )

    points = [point("reference_plane", "TP2", launch)]
    cumulative = DB(0.0)
    for i, element in enumerate(link.channel):
        cumulative = cumulative + element.loss_max.value
        points.append(
            point("loss_element", element.name, launch - cumulative, i, element.loss_max.value)
        )
    points.append(point("reference_plane", "TP3", launch - cumulative))
    return tuple(points)


def evaluate(link: Link) -> FeasibilityReport:
    results = (check_electrical(link), check_wavelength(link), check_power_budget(link))
    not_evaluated = tuple(
        CheckResult(
            constraint=cid,
            status=Status.NOT_EVALUATED,
            evidence={},
            message=NOT_EVALUATED_REASONS[cid],
        )
        for cid in ConstraintId
        if cid in NOT_EVALUATED
    )
    budget = results[2]
    margin = float(budget.evidence["margin_db"])
    return FeasibilityReport(
        link_name=link.name,
        verdict="EXCLUDED" if any(r.status is Status.FAIL for r in results) else "NOT_EXCLUDED",
        margin_db=margin,
        threshold_dbm=threshold(link).value,
        results=results,
        not_evaluated=not_evaluated,
        inputs=collect_inputs(link),
        power_trace=power_trace(link),
        upstream=upstream_section(link),
    )
