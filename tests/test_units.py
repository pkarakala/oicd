"""Tests for oicd.units. Expected values are hand calculations, not code output."""

import math
import operator

import pytest
from hypothesis import given
from hypothesis import strategies as st

from oicd.units import (
    DB,
    DBm,
    OpticalPower,
    PowerKind,
    UnitMismatchError,
    avg_to_oma,
    dbm_to_mw,
    delta_lambda_nm,
    mw_to_dbm,
)

OMA = PowerKind.OMA
AVERAGE = PowerKind.AVERAGE

# Bounded, finite floats keep hypothesis away from overflow and NaN.
levels = st.floats(min_value=-1e3, max_value=1e3, allow_nan=False, allow_infinity=False)


# --- Allowed operations -------------------------------------------------------


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        (DBm(0.0) - DB(4.0), DBm(-4.0)),
        (DBm(-4.0) + DB(1.5), DBm(-2.5)),
        (DBm(0.0) - DBm(-6.0), DB(6.0)),
        (DB(1.5) + DB(2.5), DB(4.0)),
        (DB(2.0) - DB(1.5), DB(0.5)),
        (-DB(4.0), DB(-4.0)),
    ],
    ids=["dbm-db", "dbm+db", "dbm-dbm", "db+db", "db-db", "neg-db"],
)
def test_allowed_operations(result, expected):
    assert type(result) is type(expected)
    assert result == expected


@given(a=levels, d=levels)
def test_dbm_plus_then_minus_db_round_trips(a, d):
    assert math.isclose((DBm(a) + DB(d) - DB(d)).value, a, abs_tol=1e-9)


@given(a=levels, b=levels)
def test_dbm_difference_added_back_recovers_level(a, b):
    assert math.isclose((DBm(b) + (DBm(a) - DBm(b))).value, a, abs_tol=1e-9)


@given(a=levels, b=levels)
def test_db_difference_added_back_recovers_value(a, b):
    assert math.isclose(((DB(a) - DB(b)) + DB(b)).value, a, abs_tol=1e-9)


@given(a=levels)
def test_db_double_negation_is_identity(a):
    negated = -DB(a)
    assert -negated == DB(a)


def test_model_card_t01_margin():
    # T01: 0 dBm OMA at TP2, 4.0 dB loss, -6 dBm OMA sensitivity, R = 1.5 dB.
    # Hand calc: 0 - 4.0 = -4.0 dBm; -4.0 - (-6) = 2.0 dB; 2.0 - 1.5 = 0.5 dB.
    tp2 = OpticalPower(DBm(0.0), OMA)
    s_rx = OpticalPower(DBm(-6.0), OMA)
    m_net = tp2 - DB(4.0) - s_rx - DB(1.5)
    assert m_net == DB(0.5)


def test_db_losses_sum_with_explicit_start():
    assert sum([DB(1.0), DB(2.0), DB(1.0)], start=DB(0.0)) == DB(4.0)


# --- Forbidden operations -----------------------------------------------------

# DBm + DBm is forbidden but DBm - DBm is not; it has its own test below.
FORBIDDEN_OPERANDS = [
    (DB(1.0), DBm(0.0)),
    (DBm(0.0), 1.0),
    (DBm(0.0), 1),
    (DB(1.0), 1.0),
    (DB(1.0), 1),
    (1.0, DBm(0.0)),
    (1.0, DB(1.0)),
    (0, DB(1.0)),
]


@pytest.mark.parametrize(("left", "right"), FORBIDDEN_OPERANDS)
@pytest.mark.parametrize("op", [operator.add, operator.sub], ids=["add", "sub"])
def test_forbidden_operations_raise_type_error(op, left, right):
    with pytest.raises(TypeError):
        op(left, right)


def test_dbm_plus_dbm_raises_type_error():
    with pytest.raises(TypeError):
        DBm(0.0) + DBm(0.0)


def test_db_plus_dbm_raises_type_error():
    with pytest.raises(TypeError):
        DB(1.0) + DBm(0.0)


def test_negating_dbm_raises_type_error():
    with pytest.raises(TypeError):
        -DBm(0.0)


def test_comparison_across_types_raises_type_error():
    with pytest.raises(TypeError):
        _ = DB(1.0) < DBm(1.0)


def test_db_and_dbm_with_same_number_are_not_equal():
    assert DB(1.0) != DBm(1.0)


# --- Construction -------------------------------------------------------------


@pytest.mark.parametrize("cls", [DB, DBm])
@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite_values_rejected(cls, bad):
    with pytest.raises(ValueError):
        cls(bad)


@pytest.mark.parametrize("cls", [DB, DBm])
@pytest.mark.parametrize("bad", [True, "1.0", None])
def test_non_numeric_values_rejected(cls, bad):
    with pytest.raises(TypeError):
        cls(bad)


@pytest.mark.parametrize("cls", [DB, DBm])
def test_int_is_stored_as_float(cls):
    assert type(cls(3).value) is float


@pytest.mark.parametrize("cls", [DB, DBm])
def test_values_are_immutable(cls):
    x = cls(1.0)
    with pytest.raises(AttributeError):
        x.value = 2.0


def test_optical_power_rejects_bare_float_and_bad_kind():
    with pytest.raises(TypeError):
        OpticalPower(0.0, OMA)
    with pytest.raises(TypeError):
        OpticalPower(DBm(0.0), "oma")


# --- OpticalPower and PowerKind -----------------------------------------------


@pytest.mark.parametrize("kind", [OMA, AVERAGE])
def test_optical_power_same_kind_operations(kind):
    p = OpticalPower(DBm(0.0), kind)
    assert p - DB(4.0) == OpticalPower(DBm(-4.0), kind)
    assert p + DB(1.0) == OpticalPower(DBm(1.0), kind)
    assert p - OpticalPower(DBm(-6.0), kind) == DB(6.0)


@pytest.mark.parametrize("op", [operator.add, operator.sub], ids=["add", "sub"])
def test_optical_power_mixed_kinds_raise_unit_mismatch(op):
    with pytest.raises(UnitMismatchError):
        op(OpticalPower(DBm(0.0), AVERAGE), OpticalPower(DBm(-6.0), OMA))


def test_optical_power_same_kind_addition_raises_type_error():
    with pytest.raises(TypeError) as excinfo:
        OpticalPower(DBm(0.0), OMA) + OpticalPower(DBm(0.0), OMA)
    assert not isinstance(excinfo.value, UnitMismatchError)


@pytest.mark.parametrize("op", [operator.add, operator.sub], ids=["add", "sub"])
def test_optical_power_with_bare_dbm_raises_type_error(op):
    with pytest.raises(TypeError):
        op(OpticalPower(DBm(0.0), OMA), DBm(0.0))
    with pytest.raises(TypeError):
        op(DBm(0.0), OpticalPower(DBm(0.0), OMA))


# --- Conversions --------------------------------------------------------------


def test_mw_to_dbm_reference_points():
    assert mw_to_dbm(1).value == pytest.approx(0.0, abs=1e-12)
    assert mw_to_dbm(100).value == pytest.approx(20.0, abs=1e-12)


@pytest.mark.parametrize("bad", [0.0, -1.0, math.nan, math.inf])
def test_mw_to_dbm_rejects_non_positive_or_non_finite(bad):
    with pytest.raises(ValueError):
        mw_to_dbm(bad)


def test_dbm_to_mw_reference_points():
    assert dbm_to_mw(DBm(0.0)) == pytest.approx(1.0, rel=1e-12)
    assert dbm_to_mw(DBm(20.0)) == pytest.approx(100.0, rel=1e-12)


@given(p_mw=st.floats(min_value=1e-9, max_value=1e6, allow_nan=False))
def test_mw_dbm_round_trip(p_mw):
    assert dbm_to_mw(mw_to_dbm(p_mw)) == pytest.approx(p_mw, rel=1e-12)


def test_model_card_t08_avg_to_oma():
    # T08 hand calc: ER = 10^0.4 = 2.511886; OMA = 2 * 1 mW * 1.511886 / 3.511886
    # = 0.861024 mW = -0.650 dBm.
    oma = avg_to_oma(OpticalPower(DBm(0.0), AVERAGE), DB(4.0))
    assert oma.kind is OMA
    assert oma.power_dbm.value == pytest.approx(-0.650, abs=1e-3)


def test_avg_to_oma_rejects_oma_input():
    with pytest.raises(UnitMismatchError):
        avg_to_oma(OpticalPower(DBm(0.0), OMA), DB(4.0))


@pytest.mark.parametrize("er", [0.0, -3.0])
def test_avg_to_oma_rejects_non_positive_extinction_ratio(er):
    with pytest.raises(ValueError):
        avg_to_oma(OpticalPower(DBm(0.0), AVERAGE), DB(er))


def test_avg_to_oma_rejects_bare_float_extinction_ratio():
    with pytest.raises(TypeError):
        avg_to_oma(OpticalPower(DBm(0.0), AVERAGE), 4.0)


def test_delta_lambda_200ghz_at_1310nm():
    # Hand calc: (1310e-9 m)^2 * 200e9 Hz / 299792458 m/s = 1.14487e-9 m.
    assert delta_lambda_nm(1310.0, 200.0) == pytest.approx(1.145, abs=1e-3)


@pytest.mark.parametrize("bad", [0.0, -1310.0, math.nan, math.inf])
def test_delta_lambda_rejects_bad_wavelength(bad):
    with pytest.raises(ValueError):
        delta_lambda_nm(bad, 200.0)
