"""Schema, registry and check behavior beyond the model card §5 cases."""

import pytest

from oicd.checks import CheckResult, Status
from oicd.checks.electrical import check_electrical
from oicd.checks.power_budget import check_power_budget
from oicd.checks.wavelength import check_wavelength
from oicd.provenance import Quantity
from oicd.registry import EPSILON_NM, EVALUATED, NOT_EVALUATED, ConstraintId
from oicd.schema import FEC, Link, Receiver, Transmitter
from oicd.units import DBm, OpticalPower, PowerKind, UnitMismatchError, delta_lambda_nm

# --- Registry -----------------------------------------------------------------


def test_registry_partitions_constraints():
    assert EVALUATED == {
        ConstraintId.ELECTRICAL_MATCH,
        ConstraintId.WAVELENGTH_CONTAINMENT,
        ConstraintId.OPTICAL_POWER_BUDGET,
    }
    assert NOT_EVALUATED == {
        ConstraintId.BER,
        ConstraintId.TDECQ,
        ConstraintId.DISPERSION,
        ConstraintId.REFLECTIONS_MPI,
        ConstraintId.THERMAL,
        ConstraintId.RELIABILITY,
    }
    assert EPSILON_NM == 1e-9


# --- FEC ----------------------------------------------------------------------


def test_kp4_is_an_alias_for_rs_544_514(make_link):
    link = make_link(tx_fec="KP4", rx_fec="RS(544,514)")
    assert link.tx.electrical.fec is FEC.RS_544_514
    assert check_electrical(link).status is Status.PASS


def test_unknown_fec_is_rejected(make_link):
    with pytest.raises(ValueError):
        make_link(tx_fec="RS(528,514)")


def test_fec_mismatch_fails(make_link):
    result = check_electrical(make_link(tx_fec=FEC.RS_544_514, rx_fec=FEC.NONE))
    assert result.status is Status.FAIL
    assert result.evidence["mismatched_fields"] == "fec"
    assert result.evidence["tx_fec"] == "RS(544,514)"
    assert result.evidence["rx_fec"] == "none"


# --- Electrical ---------------------------------------------------------------


def test_electrical_match_passes_with_all_fields_reported(worked_example):
    result = check_electrical(worked_example)
    assert result.status is Status.PASS
    assert result.evidence["mismatched_fields"] == ""
    for field in ("modulation", "symbol_rate_gbd", "lanes", "fec"):
        assert f"tx_{field}" in result.evidence
        assert f"rx_{field}" in result.evidence


def test_electrical_lists_every_mismatch(make_link):
    link = make_link(tx_symbol_rate_gbd=106.25, rx_symbol_rate_gbd=53.125, rx_fec=FEC.NONE)
    result = check_electrical(link)
    assert result.evidence["mismatched_fields"] == "symbol_rate_gbd, fec"


# --- Wavelength edges ---------------------------------------------------------


def test_wavelength_exact_edge_passes(make_link):
    # 1317.9 ± 2.1 nm into 1300-1320 nm: upper edge is 1320 nm on paper.
    link = make_link(tx_center_nm=1317.9, tx_tolerance_nm=2.1, rx_min_nm=1300.0, rx_max_nm=1320.0)
    assert check_wavelength(link).status is Status.PASS


def test_wavelength_edge_exact_on_paper_outside_in_float(make_link):
    # Found by search. TX: 1310 nm ± delta_lambda_nm(1310, 400 GHz) = ±2.289717375078195 nm.
    # RX upper edge: 1310 + 2 * delta_lambda_nm(1310, 200 GHz) = 1312.289717375078 nm.
    # Equal on paper (Δλ is linear in Δf), but in float TX upper = 1312.2897173750782 nm,
    # so upper_clearance_nm = -2.2737367544323206e-13. PASS only because of EPSILON_NM.
    tolerance_nm = delta_lambda_nm(1310.0, 400.0)
    half_bin_nm = delta_lambda_nm(1310.0, 200.0)
    link = make_link(
        tx_center_nm=1310.0,
        tx_tolerance_nm=tolerance_nm,
        rx_min_nm=1300.0,
        rx_max_nm=1310.0 + half_bin_nm + half_bin_nm,
    )
    result = check_wavelength(link)
    assert -EPSILON_NM < result.evidence["upper_clearance_nm"] < 0.0
    assert result.status is Status.PASS


def test_wavelength_lower_edge_outside_fails(make_link):
    link = make_link(tx_center_nm=1301.0, tx_tolerance_nm=2.0, rx_min_nm=1300.0, rx_max_nm=1320.0)
    result = check_wavelength(link)
    assert result.status is Status.FAIL
    assert result.evidence["lower_clearance_nm"] == -1.0


# --- Power budget guard -------------------------------------------------------


def test_power_budget_guard_rejects_non_oma_even_if_schema_bypassed(worked_example):
    # model_construct skips validation. Both sides AVERAGE: the OpticalPower arithmetic alone
    # would accept this (same kind), so only the OMA-only guard can reject it.
    tx, rx = worked_example.tx, worked_example.rx
    provenance = tx.launch_oma_min.provenance
    launch = Quantity(value=OpticalPower(DBm(0.0), PowerKind.AVERAGE), provenance=provenance)
    sensitivity = Quantity(value=OpticalPower(DBm(-6.0), PowerKind.AVERAGE), provenance=provenance)
    bad_tx = Transmitter.model_construct(**{**dict(tx), "launch_oma_min": launch})
    bad_rx = Receiver.model_construct(**{**dict(rx), "sensitivity_oma_max": sensitivity})
    bad_link = Link.model_construct(**{**dict(worked_example), "tx": bad_tx, "rx": bad_rx})
    with pytest.raises(UnitMismatchError):
        check_power_budget(bad_link)


# --- Results ------------------------------------------------------------------


def test_checks_are_deterministic_and_frozen(worked_example):
    for check in (check_electrical, check_wavelength, check_power_budget):
        first = check(worked_example)
        assert first == check(worked_example)
        assert isinstance(first, CheckResult)
        with pytest.raises(ValueError):
            first.status = Status.FAIL


def test_schema_models_are_frozen(worked_example):
    with pytest.raises(ValueError):
        worked_example.reserve = worked_example.reserve
