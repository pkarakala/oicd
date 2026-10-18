"""Wavelength containment (model card §3): [λ − δ, λ + δ] ⊆ [λ_RX,min, λ_RX,max]."""

from oicd.checks import CheckResult, Status
from oicd.registry import EPSILON_NM, ConstraintId
from oicd.schema import Link


def check_wavelength(link: Link) -> CheckResult:
    center_nm = link.tx.center_wavelength_nm.value
    tolerance_nm = link.tx.wavelength_tolerance_nm.value
    rx_min_nm = link.rx.passband_min_nm.value
    rx_max_nm = link.rx.passband_max_nm.value

    tx_lower_nm = center_nm - tolerance_nm
    tx_upper_nm = center_nm + tolerance_nm
    lower_clearance_nm = tx_lower_nm - rx_min_nm
    upper_clearance_nm = rx_max_nm - tx_upper_nm

    evidence: dict[str, float | str] = {
        "tx_center_nm": center_nm,
        "tx_tolerance_nm": tolerance_nm,
        "tx_lower_nm": tx_lower_nm,
        "tx_upper_nm": tx_upper_nm,
        "rx_min_nm": rx_min_nm,
        "rx_max_nm": rx_max_nm,
        "lower_clearance_nm": lower_clearance_nm,
        "upper_clearance_nm": upper_clearance_nm,
        "epsilon_nm": EPSILON_NM,
    }
    passed = lower_clearance_nm >= -EPSILON_NM and upper_clearance_nm >= -EPSILON_NM
    span = f"TX [{tx_lower_nm}, {tx_upper_nm}] nm into RX [{rx_min_nm}, {rx_max_nm}] nm"
    clearances = f"clearance lower {lower_clearance_nm} nm, upper {upper_clearance_nm} nm"
    return CheckResult(
        constraint=ConstraintId.WAVELENGTH_CONTAINMENT,
        status=Status.PASS if passed else Status.FAIL,
        evidence=evidence,
        message=f"{span}: {'contained' if passed else 'not contained'} ({clearances})",
    )
