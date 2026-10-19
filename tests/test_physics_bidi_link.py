"""Model card §13.6 and §13.7: 16λ BiDi ring leakage and the BiDi link model."""

import pytest

from oicd.physics import ring, wdm
from oicd.physics.bidi import BidiLinkRequest, evaluate_bidi_link
from oicd.provenance import SourceClass


def _direction(name: str, center_nm: float) -> dict:
    return {
        "name": name,
        "modulation": "PAM4",
        "symbol_rate_gbd": 106.25,
        "tx_oma_dbm": 2.4,
        "tx_center_nm": center_nm,
        "tx_tolerance_nm": 0.0,
        "rx_passband_min_nm": 1304.5,
        "rx_passband_max_nm": 1317.5,
        "rx_sensitivity_dbm": -4.3,
        "extra_penalties_db": {"TDECQ": 3.4, "MPI": 0.1},
    }


@pytest.fixture(scope="module")
def card_case():
    # §13.8 BiDi link model case: TX 2.4 dBm, diplexers 1.0 dB, 0.5 km at 0.4 dB/km, one 0.5 dB
    # connector, S -4.3 dBm, TDECQ 3.4 and MPI 0.1 dB, RL 15.5 dB, isolation 25 dB, R = 0.
    return evaluate_bidi_link(
        BidiLinkRequest.model_validate(
            {
                "name": "BiDi engine-style pair on the draft DR budget",
                "a_to_b": _direction("A (1311 nm)", 1311.0),
                "b_to_a": _direction("B (1331 nm)", 1331.0),
                "diplexer_il_db": 1.0,
                "diplexer_isolation_db": 25.0,
                "fiber_length_km": 0.5,
                "connector_losses_db": [0.5],
                "return_loss_db": 15.5,
            }
        )
    )


def test_bidi_case_margins_and_verdict(card_case):
    a, b = card_case.directions
    assert a.reflection.penalty_db == pytest.approx(0.000455, abs=5e-7)
    assert a.report.margin_db == pytest.approx(0.49955, abs=5e-6)
    assert b.report.margin_db == pytest.approx(0.49955, abs=5e-6)
    assert a.report.verdict == "NOT_EXCLUDED"
    assert b.report.verdict == "EXCLUDED"
    assert card_case.verdict == "EXCLUDED"
    assert card_case.deciding_direction == "B (1331 nm)"
    wl_a, wl_b = a.report.results[1].evidence, b.report.results[1].evidence
    assert (wl_a["lower_clearance_nm"], wl_a["upper_clearance_nm"]) == (6.5, 6.5)
    assert wl_b["upper_clearance_nm"] == -13.5


def test_bidi_case_min_tx_oma(card_case):
    # Minimum TX OMA = launch - margin = 2.4 - 0.49955 dBm.
    a = card_case.directions[0]
    assert a.min_tx_oma_dbm == pytest.approx(2.4 - 0.49955, abs=5e-6)


def test_bidi_case_signal_and_crosstalk_power(card_case):
    # §13.8: power at TP3 -0.3 dBm OMA = 0.933254 mW; reflected local TX 1.548817e-4 mW
    for direction in card_case.directions:
        assert direction.report.power_trace[-1].power_mw == pytest.approx(0.933254, abs=1e-6)
        assert direction.crosstalk_power_mw == pytest.approx(1.548817e-4, rel=1e-6)


def test_crosstalk_power_uses_the_local_transmitter():
    request = {
        "a_to_b": {**_direction("A", 1311.0), "tx_oma_dbm": 2.4},
        "b_to_a": {**_direction("B", 1311.0), "tx_oma_dbm": -7.6},
        "diplexer_il_db": 1.0,
        "diplexer_isolation_db": 25.0,
        "fiber_length_km": 0.5,
        "connector_losses_db": [0.5],
        "return_loss_db": 15.5,
    }
    a, b = evaluate_bidi_link(BidiLinkRequest.model_validate(request)).directions
    # A's receiver sits next to B's transmitter, 10 dB weaker than A's
    assert a.crosstalk_power_mw == pytest.approx(1.548817e-5, rel=1e-6)
    assert b.crosstalk_power_mw == pytest.approx(1.548817e-4, rel=1e-6)


def test_bidi_inputs_carry_provenance(card_case):
    report = card_case.directions[0].report
    classes = {r.path: r.source_class for r in report.inputs}
    assert classes["tx.launch_oma_min"] is SourceClass.SYNTHETIC
    fiber = next(r for r in report.inputs if r.name.startswith("fiber"))
    assert fiber.source_class is SourceClass.INFERENCE
    reflection = next(r for r in report.inputs if r.name == "reflection crosstalk")
    assert reflection.source_class is SourceClass.INFERENCE


@pytest.mark.parametrize(
    "fsr, channel, x, nrz, xr, refl",
    [
        (1800.0, 3, 0.081869, 0.3710, 1.082941, 0.2729),  # H_fsr18
        (3200.0, 7, 0.021508, 0.0944, 0.064485, 0.0158),  # H_fsr32
    ],
)
def test_16_lambda_worst_receive_channel(fsr, channel, x, nrz, xr, refl):
    # Brief 05 phase 6 values (model card §14), from the §13.6 ring model: Q 3500, IL 3 dB,
    # RL 15.5 dB, receive on odd n, transmit on even n.
    grid = wdm.interleaved_grid()
    fwhm = ring.fwhm_ghz(ring.resonance_frequency_ghz(1310.0), 3500.0)  # 65.3855 GHz, every ring
    rings = [
        wdm.ring_leakage(
            grid,
            n,
            fwhm,
            fsr,
            co=range(1, 16, 2),
            counter=range(0, 16, 2),
            modulation="NRZ",
            il_db=3.0,
            rl_db=15.5,
        )
        for n in range(1, 16, 2)
    ]
    worst = wdm.worst_channel(grid, rings)
    assert worst.channel == channel
    assert worst.leakage == pytest.approx(x, abs=5e-7)
    assert worst.crosstalk_db == pytest.approx(nrz, abs=5e-5)
    assert worst.reflected_leakage == pytest.approx(xr, abs=5e-7)
    assert worst.reflection_db == pytest.approx(refl, abs=5e-5)


def test_fsr18_images_on_local_transmitters():
    # Under H_fsr18 seven of eight receive rings (all but channel 7) have an image exactly on a
    # local transmit channel.
    grid = wdm.interleaved_grid()
    hits = [
        n
        for n in range(1, 16, 2)
        if any(i.direction == "counter" for i in wdm.aliasing(grid, n, 1800.0, range(0, 16, 2)))
    ]
    assert hits == [1, 3, 5, 9, 11, 13, 15]
