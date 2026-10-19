"""Model card §8: design-space sweep. Expected values are copied from the card."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from oicd.paths import get_input, set_input
from oicd.registry import EPSILON_DB
from oicd.report import evaluate
from oicd.sweep import MAX_AXIS_POINTS, linspace, sweep

from .conftest import build_chain, with_chain

PATCH = "channel[2].loss_max"  # §4 channel in §2 order: the patch connector is element 2
TX_OMA = "tx.launch_oma_min"


@pytest.fixture(scope="module")
def card_grid(worked_example):
    # §8 hand cases: patch loss 0 to 2 dB, TX OMA -1 to +1 dBm.
    return sweep(worked_example, PATCH, linspace(0.0, 2.0, 21), TX_OMA, linspace(-1.0, 1.0, 21))


def cell(result, x, y):
    return result.margin_db[result.y.values.index(y)][result.x.values.index(x)]


def test_hand_cases(card_grid):
    # §8: (1.0, 0) -> +0.4992; (2.0, 0) -> -0.5008; (0, +1) -> +2.4992.
    assert cell(card_grid, 1.0, 0.0) == pytest.approx(0.4992, abs=1e-12)
    assert cell(card_grid, 2.0, 0.0) == pytest.approx(-0.5008, abs=1e-12)
    assert cell(card_grid, 0.0, 1.0) == pytest.approx(2.4992, abs=1e-12)
    assert card_grid.x.unit == "dB" and card_grid.y.unit == "dBm OMA"


def test_slopes(card_grid):
    # §8: slope -1 dB per dB of patch loss, +1 dB per dB of TX OMA.
    xs, ys, m = card_grid.x.values, card_grid.y.values, card_grid.margin_db
    for j in range(len(ys)):
        for i in range(len(xs) - 1):
            assert m[j][i + 1] - m[j][i] == pytest.approx(-(xs[i + 1] - xs[i]), abs=1e-12)
    for j in range(len(ys) - 1):
        for i in range(len(xs)):
            assert m[j + 1][i] - m[j][i] == pytest.approx(ys[j + 1] - ys[j], abs=1e-12)


def test_verdict_grid_follows_the_margin(card_grid):
    for row_m, row_v in zip(card_grid.margin_db, card_grid.verdict, strict=True):
        for m, v in zip(row_m, row_v, strict=True):
            assert v == ("NOT_EXCLUDED" if m >= -EPSILON_DB else "EXCLUDED")


def test_design_best_worst(card_grid):
    assert (card_grid.design.i, card_grid.design.j) == (10, 10)
    assert card_grid.design.margin_db == pytest.approx(0.4992, abs=1e-12)
    assert card_grid.design.margin_db == cell(card_grid, 1.0, 0.0)
    assert (card_grid.best.x, card_grid.best.y) == (0.0, 1.0)
    assert (card_grid.worst.x, card_grid.worst.y) == (2.0, -1.0)
    assert card_grid.worst.margin_db == pytest.approx(-1.5008, abs=1e-12)


def test_contour_lies_on_zero_margin(card_grid):
    # M = 0.4992 - (x - 1.0) + y on this grid, so every contour point has M = 0.
    assert card_grid.contour_0db
    for segment in card_grid.contour_0db:
        for x, y in segment:
            assert 0.4992 - (x - 1.0) + y == pytest.approx(0.0, abs=1e-9)


@settings(max_examples=30, deadline=None)
@given(i=st.integers(min_value=0, max_value=20), j=st.integers(min_value=0, max_value=20))
def test_cell_equals_evaluate_bit_for_bit(card_grid, worked_example, i, j):
    x, y = card_grid.x.values[i], card_grid.y.values[j]
    edited = set_input(set_input(worked_example, PATCH, x), TX_OMA, y)
    report = evaluate(edited)
    assert card_grid.margin_db[j][i] == report.margin_db
    assert card_grid.verdict[j][i] == report.verdict


def test_wavelength_axes_set_the_verdict_not_the_margin(worked_example):
    # TX 1310 ± 2 nm into 1300 to 1320 nm (T09): the centre swept 1300 to 1320 nm.
    result = sweep(
        worked_example,
        "tx.center_wavelength_nm",
        linspace(1300.0, 1320.0, 21),
        "tx.wavelength_tolerance_nm",
        (0.0, 2.0, 5.0),
    )
    for j, tol in enumerate(result.y.values):
        for i, center in enumerate(result.x.values):
            assert result.margin_db[j][i] == pytest.approx(0.4992, abs=1e-12)
            contained = center - tol >= 1300.0 and center + tol <= 1320.0
            assert result.verdict[j][i] == ("NOT_EXCLUDED" if contained else "EXCLUDED")
    assert result.contour_0db == ()


def test_upstream_axes_match_evaluate(worked_example):
    # §10 chain: sweeping N and the modulator IL gives the same cells as evaluate().
    link = with_chain(worked_example, build_chain())
    result = sweep(
        link,
        "tx.upstream.split_n",
        (1, 8, 16, 17, 18, 32),
        "tx.upstream.modulator_il",
        (3.0, 4.0, 5.0),
    )
    for j, mod in enumerate(result.y.values):
        for i, n in enumerate(result.x.values):
            edited = set_input(
                set_input(link, "tx.upstream.split_n", n), "tx.upstream.modulator_il", mod
            )
            assert result.margin_db[j][i] == evaluate(edited).margin_db
    assert get_input(link, "tx.upstream.split_n") == 16.0


@pytest.mark.parametrize(
    "x_path, x_values, y_path, message",
    [
        ("channel[9].loss_max", (0.0, 1.0), TX_OMA, "no input"),
        ("bogus.path", (0.0, 1.0), TX_OMA, "unknown input path"),
        (PATCH, tuple(float(v) for v in range(MAX_AXIS_POINTS + 1)), TX_OMA, "1 to 201"),
        (PATCH, (1.0, 0.0), TX_OMA, "strictly increasing"),
        (PATCH, (-1.0, 0.0), TX_OMA, "loss_max"),
        (PATCH, (0.0, 1.0), PATCH, "different inputs"),
        ("tx.upstream.split_n", (1.0, 2.0), TX_OMA, "fixed TP2"),
    ],
)
def test_invalid_sweeps_raise(worked_example, x_path, x_values, y_path, message):
    with pytest.raises((KeyError, ValueError), match=message):
        sweep(worked_example, x_path, x_values, y_path, (0.0, 1.0))


def test_crossed_passband_grid_is_invalid(worked_example):
    with pytest.raises(ValueError, match="passband_min_nm must be < passband_max_nm"):
        sweep(
            worked_example,
            "rx.passband_min_nm",
            (1300.0, 1315.0),
            "rx.passband_max_nm",
            (1310.0, 1320.0),
        )


def test_linspace_limits():
    assert linspace(0.0, 2.0, 3) == (0.0, 1.0, 2.0)
    with pytest.raises(ValueError):
        linspace(0.0, 1.0, MAX_AXIS_POINTS + 1)
