"""Electrical interface match (model card §3): modulation, symbol rate, lanes and FEC."""

from oicd.checks import CheckResult, Status
from oicd.registry import ConstraintId
from oicd.schema import Link

_FIELDS = ("modulation", "symbol_rate_gbd", "lanes", "fec")


def _evidence_value(value: object) -> float | str:
    if isinstance(value, str):
        return str(value)
    if isinstance(value, (int, float)):
        return float(value)
    raise TypeError(f"unexpected evidence value {value!r}")


def check_electrical(link: Link) -> CheckResult:
    tx = link.tx.electrical
    rx = link.rx.electrical
    evidence: dict[str, float | str] = {}
    mismatched: list[str] = []
    for field in _FIELDS:
        tx_value = getattr(tx, field)
        rx_value = getattr(rx, field)
        evidence[f"tx_{field}"] = _evidence_value(tx_value)
        evidence[f"rx_{field}"] = _evidence_value(rx_value)
        if tx_value != rx_value:
            mismatched.append(field)
    evidence["mismatched_fields"] = ", ".join(mismatched)

    if mismatched:
        details = "; ".join(
            f"{field}: TX {evidence[f'tx_{field}']} vs RX {evidence[f'rx_{field}']}"
            for field in mismatched
        )
        return CheckResult(
            constraint=ConstraintId.ELECTRICAL_MATCH,
            status=Status.FAIL,
            evidence=evidence,
            message=f"Electrical mismatch on {details}",
        )
    return CheckResult(
        constraint=ConstraintId.ELECTRICAL_MATCH,
        status=Status.PASS,
        evidence=evidence,
        message="TX and RX match on modulation, symbol_rate_gbd, lanes and fec",
    )
