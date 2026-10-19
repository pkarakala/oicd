"""Model card §9: multi-lane tray. Expected values are copied from the card."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from oicd.paths import set_input
from oicd.tray import MAX_LANES, evaluate_tray


def test_hand_case(worked_example):
    # §9: 8 copies of the worked example, lane 5 patch connector 2.0 dB -> tray margin -0.5008,
    # deciding lane 5, EXCLUDED.
    lanes = [worked_example] * 8
    lanes[5] = set_input(worked_example, "channel[2].loss_max", 2.0)
    tray = evaluate_tray(lanes)
    assert tray.verdict == "EXCLUDED"
    assert tray.margin_db == pytest.approx(-0.5008, abs=1e-12)
    assert tray.deciding_lane == 5
    assert tray.excluded_lanes == (5,)
    assert tray.lane_count == 8
    for lane in tray.lanes:
        expected = -0.5008 if lane.index == 5 else 0.4992
        assert lane.margin_db == pytest.approx(expected, abs=1e-12)
    assert tray.deciding_report.margin_db == tray.margin_db


def test_ties_go_to_the_lowest_index(worked_example):
    tray = evaluate_tray([worked_example] * 4)
    assert tray.verdict == "NOT_EXCLUDED"
    assert tray.deciding_lane == 0
    assert tray.excluded_lanes == ()


def test_excluded_lane_decides_even_with_a_larger_margin(make_link):
    # Lane 1 fails on wavelength (T10) with M = +0.5 dB; lane 0 passes with M = +0.1 dB.
    lanes = [
        make_link(channel_db=(("c", 4.4),)),
        make_link(tx_center_nm=1318.0, tx_tolerance_nm=3.0),
    ]
    tray = evaluate_tray(lanes)
    assert tray.verdict == "EXCLUDED"
    assert tray.deciding_lane == 1
    assert tray.margin_db == pytest.approx(0.1, abs=1e-12)
    assert tray.lanes[1].failed == ("wavelength_containment",)


lane_losses = st.lists(st.floats(min_value=0.0, max_value=8.0), min_size=1, max_size=6)


@given(losses=lane_losses, extra=st.floats(min_value=0.0, max_value=8.0))
def test_adding_a_lane_never_raises_the_tray_margin(make_link, losses, extra):
    lanes = [make_link(channel_db=(("c", v),)) for v in losses]
    before = evaluate_tray(lanes).margin_db
    after = evaluate_tray([*lanes, make_link(channel_db=(("c", extra),))]).margin_db
    assert after <= before


def test_lane_count_limits(worked_example):
    with pytest.raises(ValueError):
        evaluate_tray([])
    with pytest.raises(ValueError):
        evaluate_tray([worked_example] * (MAX_LANES + 1))
