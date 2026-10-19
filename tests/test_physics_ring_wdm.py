"""Model card §13: microring and WDM link physics. Expected values are copied from §13.8."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from oicd.physics import ring, wdm

F0 = ring.resonance_frequency_ghz(1310.0)
FWHM = ring.fwhm_ghz(F0, 3500.0)


def test_f0_and_fwhm():
    assert F0 / 1000 == pytest.approx(228.8492, abs=5e-5)
    assert FWHM == pytest.approx(65.3855, abs=5e-5)


def test_neighbor_rejection_and_interleaving_gain():
    at400 = ring.db(ring.lorentzian(400.0, FWHM))
    at200 = ring.db(ring.lorentzian(200.0, FWHM))
    assert at400 == pytest.approx(-21.781, abs=5e-4)
    assert at200 == pytest.approx(-15.846, abs=5e-4)
    assert at200 - at400 == pytest.approx(5.935, abs=5e-4)


@pytest.mark.parametrize(
    "spacing, x, nrz, pam4",
    [(400.0, 0.013272, 0.0580, 0.1764), (200.0, 0.052050, 0.2321, 0.7373)],
)
def test_two_neighbor_crosstalk(spacing, x, nrz, pam4):
    # §13.8: single Lorentzian, images excluded.
    leak = 2 * ring.lorentzian(spacing, FWHM)
    assert leak == pytest.approx(x, abs=5e-7)
    assert ring.crosstalk_penalty(leak, "NRZ").penalty_db == pytest.approx(nrz, abs=5e-5)
    assert ring.crosstalk_penalty(leak, "PAM4").penalty_db == pytest.approx(pam4, abs=5e-5)


def test_alternative_form():
    # §13.8: 10·log10(1 + X) = 0.0573 dB (X400), 0.2204 dB (X200).
    assert ring.crosstalk_penalty(0.013272, "NRZ").alternative_db == pytest.approx(0.0573, abs=5e-5)
    assert ring.crosstalk_penalty(0.052050, "NRZ").alternative_db == pytest.approx(0.2204, abs=5e-5)


def test_crosstalk_closed_eye_is_invalid():
    with pytest.raises(ValueError, match="eye is closed"):
        ring.crosstalk_penalty(0.34, "PAM4")
    with pytest.raises(ValueError):
        ring.crosstalk_penalty(-0.01, "NRZ")


def test_fsr_and_group_index():
    # §13.8: FSR 1.8 THz = 10.3037 nm = 9 slots; n_g for a 15 µm diameter = 3.5343.
    assert ring.span_nm(1800.0, 1310.0) == pytest.approx(10.3037, abs=5e-5)
    length = ring.circumference_um(15.0)
    assert ring.group_index_from_fsr(1800.0, length) == pytest.approx(3.5343, abs=5e-5)
    ng = ring.group_index_from_fsr(1800.0, length)
    assert ring.fsr_ghz(ng, length) == pytest.approx(1800.0, rel=1e-12)
    assert ring.fsr_nm(1310.0, ng, length) == pytest.approx(10.3037, abs=5e-5)


def test_max_radius_for_a_unique_channel():
    # §13.8: R ≤ 3.5501 µm at n_g 4.2 for one FSR ≥ 3.2 THz.
    assert ring.max_radius_um(4.2, 3200.0) == pytest.approx(3.5501, abs=5e-5)


@pytest.mark.parametrize(
    "baud, spacing, q_min, q_max, is_open, q_inside",
    [
        (56.0, 200.0, 3166.0, 5448.8, True, True),
        (56.0, 400.0, 1583.0, 5448.8, True, True),
        (106.25, 200.0, 3166.0, 2871.8, False, False),
        (106.25, 400.0, 1583.0, 2871.8, True, False),
    ],
)
def test_design_windows(baud, spacing, q_min, q_max, is_open, q_inside):
    window = ring.design_window(F0, spacing, baud, q=3500.0)
    assert window.q_min == pytest.approx(q_min, abs=0.05)
    assert window.q_max == pytest.approx(q_max, abs=0.05)
    assert window.open is is_open
    assert window.q_inside is q_inside


@pytest.mark.parametrize(
    "span_ghz, nm, mw", [(200.0, 1.1449, 2.6020), (400.0, None, 5.2039), (1800.0, None, 23.4176)]
)
def test_heater_power(span_ghz, nm, mw):
    tuning = ring.span_nm(span_ghz, 1310.0)
    if nm is not None:
        assert tuning == pytest.approx(nm, abs=5e-5)
    assert ring.heater_power_mw(tuning, 0.44) == pytest.approx(mw, abs=5e-5)


def test_thermal_tuning_barrel_shifting():
    # §13.4: one spacing with barrel shifting, one FSR without; laser ±20 GHz = 0.11449 nm.
    common = dict(
        wavelength_nm=1310.0,
        laser_accuracy_ghz=20.0,
        fabrication_offset_nm=1.0,
        drift_nm_per_k=0.07,
        temperature_swing_k=10.0,
        spacing_ghz=400.0,
        fsr_ghz=1800.0,
        efficiency_nm_per_mw=0.44,
    )
    with_bs = ring.thermal_tuning(**common, barrel_shifting=True)
    without = ring.thermal_tuning(**common, barrel_shifting=False)
    assert with_bs.laser_accuracy_nm == pytest.approx(0.11449, abs=5e-6)
    assert with_bs.required_nm == pytest.approx(0.11449 + 1.0 + 0.7, abs=5e-5)
    assert with_bs.heater_power_mw == pytest.approx(5.2039, abs=5e-5)
    assert without.heater_power_mw == pytest.approx(23.4176, abs=5e-5)
    assert with_bs.exceeds_range is False and without.exceeds_range is False


def test_thermal_drift_upper_bound():
    # §13.1: 1310 nm × 1.94e-4 /K / 3.5343 = 0.0719 nm/K.
    assert ring.thermal_drift_nm_per_k(1310.0, 1.94e-4, 3.5343) == pytest.approx(0.0719, abs=5e-5)


def test_guide_grid():
    # §13.8: λ_0 1318.6431 nm, λ_15 1301.4695 nm, span 17.1736 nm; even A, odd B.
    grid = wdm.interleaved_grid()
    assert grid.channels[0].wavelength_nm == pytest.approx(1318.6431, abs=5e-5)
    assert grid.channels[15].wavelength_nm == pytest.approx(1301.4695, abs=5e-5)
    assert grid.span_nm == pytest.approx(17.1736, abs=5e-5)
    assert [c.grid for c in grid.channels[:4]] == ["A", "B", "A", "B"]
    assert grid.source_class == "inference"


def test_aliasing_channel_0():
    # §13.8: a ring on channel 0 with FSR 1.8 THz has its image on channel 9 (grid B).
    grid = wdm.interleaved_grid()
    images = wdm.aliasing(grid, 0, 1800.0, counter=range(1, 16, 2))
    # Channel 9 is 9 × 200 GHz = 1.8 THz above channel 0: the first image above (order +1).
    assert [(i.channel, i.order, i.direction) for i in images] == [(9, 1, "counter")]


@given(
    near=st.floats(min_value=50.0, max_value=1000.0),
    extra=st.floats(min_value=1.0, max_value=1000.0),
)
def test_crosstalk_falls_with_spacing(near, extra):
    assert ring.lorentzian(near + extra, FWHM) < ring.lorentzian(near, FWHM)


@given(
    x=st.floats(min_value=0.0, max_value=0.3),
    dx=st.floats(min_value=1e-6, max_value=0.02),
)
def test_penalty_rises_with_leakage(x, dx):
    for mod in ("NRZ", "PAM4"):
        if ring.EYE_FACTOR[mod] * (x + dx) < 1.0:
            assert (
                ring.crosstalk_penalty(x + dx, mod).penalty_db
                > ring.crosstalk_penalty(x, mod).penalty_db
            )


@given(tuning=st.floats(min_value=0.0, max_value=20.0), k=st.floats(min_value=0.0, max_value=5.0))
def test_heater_power_is_linear(tuning, k):
    assert ring.heater_power_mw(k * tuning, 0.44) == pytest.approx(
        k * ring.heater_power_mw(tuning, 0.44), rel=1e-12, abs=1e-12
    )


def test_drop_response_is_periodic():
    # Periodic up to the truncation of the image sum at k = ±50: a one-FSR shift swaps the
    # outermost image in or out, a relative change of a few 1e-6.
    for detuning in (0.0, 100.0, 650.0):
        a = ring.drop_response(detuning, FWHM, 1800.0)
        b = ring.drop_response(detuning + 1800.0, FWHM, 1800.0)
        assert a == pytest.approx(b, rel=1e-5)


def test_ring_summary():
    summary = ring.ring_summary(1310.0, 3500.0, fsr_ghz_value=1800.0, diameter_um=15.0)
    assert summary.fwhm_ghz == pytest.approx(65.3855, abs=5e-5)
    assert summary.group_index == pytest.approx(3.5343, abs=5e-5)
    assert summary.neighbor_rejection_db["200"] == pytest.approx(-15.846, abs=5e-4)
    with pytest.raises(ValueError):
        ring.ring_summary(1310.0, 3500.0)


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan"), float("inf")])
def test_invalid_ring_inputs(bad):
    with pytest.raises(ValueError):
        ring.fwhm_ghz(F0, bad)
    with pytest.raises(ValueError):
        ring.resonance_frequency_ghz(bad)
