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
from oicd.registry import NOT_EVALUATED, ConstraintId
from oicd.schema import Link
from oicd.units import DB, DBm

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
    are None at the reference planes. headroom_db = power_dbm − threshold_dbm.
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
        _record(
            "tx.launch_oma_min",
            tx.name,
            tx.launch_oma_min.value.power_dbm.value,
            f"dBm {tx.launch_oma_min.value.kind.value.upper()}",
            tx.launch_oma_min.provenance,
        ),
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


def threshold(link: Link) -> DBm:
    """Required OMA at TP3: S_RX,OMA,max + Σ Π_j + R (model card §3 rearranged)."""
    penalties = sum((p.value.value for p in link.penalties), start=DB(0.0))
    return link.rx.sensitivity_oma_max.value.power_dbm + penalties + link.reserve.value


def power_trace(link: Link) -> tuple[TracePoint, ...]:
    """OMA at TP2, after each loss element, and at TP3.

    Losses are accumulated in channel order with the same start and order as the power-budget
    check, so the TP3 point equals the check's p_tp3_dbm exactly.
    """
    launch = link.tx.launch_oma_min.value.power_dbm
    thr = threshold(link)
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
        return TracePoint(
            kind=kind,
            name=name,
            channel_index=index,
            input_path=None if index is None else f"channel[{index}].loss_max",
            power_dbm=power.value,
            loss_db=None if loss is None else loss.value,
            loss_fraction=fraction,
            headroom_db=(power - thr).value,
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
    )
