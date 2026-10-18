"""Model card §4 worked example and §5 cases T01 to T12.

Expected values are copied from docs/model_card.md, not computed by the code.
Unless stated, inputs are T01's: P_TP2 = 0 dBm OMA, S_RX = -6 dBm OMA, Π = 0, R = 1.5 dB.
"""

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from oicd.checks import Status
from oicd.checks.electrical import check_electrical
from oicd.checks.power_budget import check_power_budget
from oicd.checks.wavelength import check_wavelength
from oicd.registry import EPSILON_DB
from oicd.units import DB, DBm, OpticalPower, PowerKind, UnitMismatchError, avg_to_oma


def test_worked_example(worked_example):
    # §4: Σ L = 4.0008 dB, P_TP3 = -4.0008 dBm OMA, M_net = +0.4992 dB, PASS.
    result = check_power_budget(worked_example)
    assert result.evidence["total_loss_db"] == pytest.approx(4.0008, abs=1e-12)
    assert result.evidence["p_tp3_dbm"] == pytest.approx(-4.0008, abs=1e-12)
    assert result.evidence["margin_db"] == pytest.approx(0.4992, abs=1e-12)
    assert result.status is Status.PASS


def test_T01_nominal_pass(make_link):
    # T01: loss 4.0 dB -> M = +0.5 dB, PASS.
    result = check_power_budget(make_link(channel_db=(("channel", 4.0),)))
    assert result.evidence["margin_db"] == 0.5
    assert result.status is Status.PASS


def test_T02_nominal_fail(make_link):
    # T02: loss 5.0 dB -> M = -0.5 dB, FAIL.
    result = check_power_budget(make_link(channel_db=(("channel", 5.0),)))
    assert result.evidence["margin_db"] == -0.5
    assert result.status is Status.FAIL


def test_T03_exact_boundary(make_link):
    # T03: loss 4.5 dB -> M = 0.0 dB, PASS (>= -ε).
    result = check_power_budget(make_link(channel_db=(("channel", 4.5),)))
    assert result.evidence["margin_db"] == 0.0
    assert result.status is Status.PASS


def test_T04_boundary_with_non_representable_floats(make_link):
    # T04: losses 0.3 + 1.3 + 3.3 dB, R = 1.1 dB. Exact M = 0; float M = -4.44e-16;
    # PASS only because of ε. Per the card, assert PASS and |M| < 1e-9, not the exact float.
    link = make_link(channel_db=(("a", 0.3), ("b", 1.3), ("c", 3.3)), reserve_db=1.1)
    result = check_power_budget(link)
    assert abs(result.evidence["margin_db"]) < 1e-9
    assert result.status is Status.PASS


def test_T05_loss_monotonicity(make_link):
    # T05: T01 plus one 0.5 dB connector -> M drops by exactly 0.5 to 0.0 dB, PASS.
    t01 = check_power_budget(make_link(channel_db=(("channel", 4.0),)))
    t05 = check_power_budget(make_link(channel_db=(("channel", 4.0), ("connector", 0.5))))
    assert t01.evidence["margin_db"] - t05.evidence["margin_db"] == 0.5
    assert t05.evidence["margin_db"] == 0.0
    assert t05.status is Status.PASS


loss_db = st.floats(min_value=0.0, max_value=20.0, allow_nan=False, allow_infinity=False)


@given(
    losses=st.lists(loss_db, max_size=6),
    extra=loss_db,
    position=st.integers(min_value=0, max_value=6),
)
def test_T05_property_adding_loss_never_raises_margin(make_link, losses, extra, position):
    # T05 property: adding any loss >= 0, anywhere in the channel, never raises M.
    position = min(position, len(losses))
    before = [(f"l{i}", v) for i, v in enumerate(losses)]
    after = before[:position] + [("extra", extra)] + before[position:]
    m_before = check_power_budget(make_link(channel_db=tuple(before))).evidence["margin_db"]
    m_after = check_power_budget(make_link(channel_db=tuple(after))).evidence["margin_db"]
    assert m_after <= m_before


def test_T06_named_penalty(make_link):
    # T06: T01 with Π = 1.0 dB -> M = -0.5 dB, FAIL; the result names the penalty.
    link = make_link(channel_db=(("channel", 4.0),), penalties_db=(("TDECQ", 1.0),))
    result = check_power_budget(link)
    assert result.evidence["margin_db"] == -0.5
    assert result.evidence["penalties_db"] == 1.0
    assert result.status is Status.FAIL
    assert result.evidence["penalty_names"] == "TDECQ"
    assert "TDECQ" in result.message


@pytest.mark.parametrize(
    "kinds",
    [
        {"launch_kind": PowerKind.AVERAGE},
        {"sensitivity_kind": PowerKind.AVERAGE},
    ],
    ids=["tx-average", "rx-average"],
)
def test_T07_oma_average_mixing(make_link, kinds):
    # T07: TX AVERAGE, RX OMA -> raises UnitMismatchError (at schema construction).
    with pytest.raises(UnitMismatchError):
        make_link(**kinds)


def test_T08_average_to_oma():
    # T08: P_avg = 0 dBm, ER = 4 dB -> OMA = -0.650 dBm (-0.64991).
    oma = avg_to_oma(OpticalPower(DBm(0.0), PowerKind.AVERAGE), DB(4.0))
    assert oma.kind is PowerKind.OMA
    assert oma.power_dbm.value == pytest.approx(-0.64991, abs=1e-5)


def test_T09_wavelength_inside_passband(make_link):
    # T09: TX 1310 ± 2 nm, RX 1300 to 1320 nm -> PASS; 8 nm clearance each side.
    link = make_link(tx_center_nm=1310.0, tx_tolerance_nm=2.0, rx_min_nm=1300.0, rx_max_nm=1320.0)
    result = check_wavelength(link)
    assert result.status is Status.PASS
    assert result.evidence["lower_clearance_nm"] == 8.0
    assert result.evidence["upper_clearance_nm"] == 8.0


def test_T10_wavelength_edge_outside(make_link):
    # T10: TX 1318 ± 3 nm, RX 1300 to 1320 nm -> FAIL; upper edge 1321 nm exceeds 1320 by 1 nm.
    link = make_link(tx_center_nm=1318.0, tx_tolerance_nm=3.0, rx_min_nm=1300.0, rx_max_nm=1320.0)
    result = check_wavelength(link)
    assert result.status is Status.FAIL
    assert result.evidence["tx_upper_nm"] == 1321.0
    assert result.evidence["upper_clearance_nm"] == -1.0


def test_T11_electrical_mismatch(make_link):
    # T11: TX 106.25 GBd PAM4, RX 53.125 GBd PAM4 -> FAIL on symbol_rate_gbd;
    # modulation, lanes, FEC still reported.
    link = make_link(tx_symbol_rate_gbd=106.25, rx_symbol_rate_gbd=53.125, modulation="PAM4")
    result = check_electrical(link)
    assert result.status is Status.FAIL
    assert result.evidence["mismatched_fields"] == "symbol_rate_gbd"
    assert result.evidence["tx_symbol_rate_gbd"] == 106.25
    assert result.evidence["rx_symbol_rate_gbd"] == 53.125
    for field in ("modulation", "lanes", "fec"):
        assert result.evidence[f"tx_{field}"] == result.evidence[f"rx_{field}"]
    assert "symbol_rate_gbd" in result.message


@pytest.mark.parametrize(
    "bad",
    [
        {"channel_db": (("negative loss", -0.1),)},
        {"tx_center_nm": 0.0},
        {"tx_center_nm": math.nan},
        {"tx_tolerance_nm": -0.5},
        {"rx_min_nm": 0.0},
        {"rx_min_nm": 1320.0, "rx_max_nm": 1300.0},
        {"rx_min_nm": 1310.0, "rx_max_nm": 1310.0},
        {"rx_max_nm": math.inf},
        {"penalties_db": (("negative penalty", -1.0),)},
        {"reserve_db": -0.1},
        {"tx_symbol_rate_gbd": 0.0},
        {"lanes": 0},
        {"modulation": "PAM8"},
    ],
    ids=lambda bad: ",".join(bad),
)
def test_T12_invalid_physics(make_link, bad):
    # T12: negative loss, 0 nm wavelength (and other invalid physics) -> ValueError at schema.
    with pytest.raises(ValueError):
        make_link(**bad)


@pytest.mark.parametrize("er_db", [0.0, -1.0])
def test_T12_extinction_ratio_not_positive(er_db):
    # T12: ER <= 0 dB -> ValueError. The schema has no ER field; the conversion rejects it.
    with pytest.raises(ValueError):
        avg_to_oma(OpticalPower(DBm(0.0), PowerKind.AVERAGE), DB(er_db))


def test_epsilon_matches_model_card():
    # §3: ε = 1e-9 dB.
    assert EPSILON_DB == 1e-9
