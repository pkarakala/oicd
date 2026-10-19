"""Physics endpoints: /ring, /wdm/grid, /wdm/crosstalk, /bidi/link, /mpi, /rack, /pod. Expected
values from model card §12, §13 and §14."""

import pytest
from fastapi.testclient import TestClient

from oicd.api import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_ring(client):
    body = {
        "q_loaded": 3500,
        "fsr_ghz": 1800,
        "diameter_um": 15,
        "symbol_rates_gbd": [56, 106.25],
        "spectrum_span_ghz": 400,
        "spectrum_points": 401,
    }
    r = client.post("/ring", json=body).json()
    assert r["summary"]["fwhm_ghz"] == pytest.approx(65.3855, abs=5e-5)
    assert r["summary"]["fsr_nm"] == pytest.approx(10.3037, abs=5e-5)
    assert r["summary"]["group_index"] == pytest.approx(3.5343, abs=5e-5)
    windows = {(w["symbol_rate_gbd"], w["spacing_ghz"]): w for w in r["windows"]}
    assert windows[(56, 200)]["open"] is True and windows[(56, 200)]["q_inside"] is True
    assert windows[(106.25, 200)]["open"] is False
    spectrum = r["spectrum"]
    peak = max(range(401), key=lambda i: spectrum["drop"][i])
    # §13.1: the image sum peaks 0.0047 dB above 1 at Q 3500 and FSR 1.8 THz.
    assert peak == 200 and spectrum["drop_db"][200] == pytest.approx(0.0047, abs=1e-4)


def test_wdm_grid(client):
    grid = client.post("/wdm/grid", json={}).json()
    assert grid["channels"][0]["wavelength_nm"] == pytest.approx(1318.6431, abs=5e-5)
    assert grid["channels"][15]["wavelength_nm"] == pytest.approx(1301.4695, abs=5e-5)
    assert grid["source_class"] == "inference"


@pytest.mark.parametrize(
    "fsr, channel, x, refl", [(1800, 3, 0.081869, 0.2729), (3200, 7, 0.021508, 0.0158)]
)
def test_wdm_crosstalk(client, fsr, channel, x, refl):
    body = {"q_loaded": 3500, "fsr_ghz": fsr, "il_db": 3, "rl_db": 15.5, "spectrum_points": 201}
    r = client.post("/wdm/crosstalk", json=body).json()
    assert r["worst"]["channel"] == channel
    assert r["worst"]["leakage"] == pytest.approx(x, abs=5e-7)
    assert r["worst"]["reflection_db"] == pytest.approx(refl, abs=5e-5)
    assert r["receive_channels"] == [1, 3, 5, 7, 9, 11, 13, 15]
    assert len(r["spectra"]) == 8 and len(r["spectra"][0]["drop_db"]) == 201


def test_wdm_crosstalk_closed_eye_is_422(client):
    body = {"q_loaded": 100, "fsr_ghz": 1800, "modulation": "PAM4"}
    assert client.post("/wdm/crosstalk", json=body).status_code == 422


def test_bidi_link(client):
    def direction(name, center):
        return {
            "name": name,
            "modulation": "PAM4",
            "symbol_rate_gbd": 106.25,
            "tx_oma_dbm": 2.4,
            "tx_center_nm": center,
            "tx_tolerance_nm": 0.0,
            "rx_passband_min_nm": 1304.5,
            "rx_passband_max_nm": 1317.5,
            "rx_sensitivity_dbm": -4.3,
            "extra_penalties_db": {"TDECQ": 3.4, "MPI": 0.1},
        }

    body = {
        "a_to_b": direction("A", 1311.0),
        "b_to_a": direction("B", 1331.0),
        "diplexer_il_db": 1.0,
        "diplexer_isolation_db": 25.0,
        "fiber_length_km": 0.5,
        "connector_losses_db": [0.5],
        "return_loss_db": 15.5,
    }
    r = client.post("/bidi/link", json=body).json()
    assert r["verdict"] == "EXCLUDED"
    assert r["deciding_direction"] == "B"
    assert r["directions"][0]["report"]["margin_db"] == pytest.approx(0.49955, abs=5e-6)


def test_mpi(client):
    body = {
        "m_levels": 4,
        "er_db": 6,
        "rt_db": -20,
        "rr_db": -26,
        "rc_db": -35,
        "n_connectors": 2,
        "n_max": 6,
    }
    r = client.post("/mpi", json=body).json()
    assert r["result"]["penalty_db"] == pytest.approx(0.8142, abs=5e-5)
    table = {row["n_connectors"]: row["penalty_db"] for row in r["table"]}
    assert table[4] == pytest.approx(1.4378, abs=5e-5)
    assert table[6] == pytest.approx(2.3137, abs=5e-5)


def test_mpi_diverging_bound_is_422(client):
    body = {"m_levels": 4, "er_db": 6, "rt_db": -10, "rr_db": -10, "rc_db": -10, "n_connectors": 6}
    assert client.post("/mpi", json=body).status_code == 422


def test_rack(client):
    r = client.post("/rack", json={}).json()
    margins = sorted(round(p["report"]["margin_db"], 4) for p in r["paths"])
    assert margins == [-1.0016, -0.0016, 1.9984]
    assert r["link_yield_needed"] == pytest.approx(0.99999877, abs=5e-9)
    assert r["z_needed"] == pytest.approx(4.712, abs=5e-4)
    assert {s["hypothesis"]: s["ou_used"] for s in r["space"]} == {"H_2U": 42, "H_1U": 26}
    assert client.post("/rack", json={"link_yields": [1.5]}).status_code == 422


def test_pod(client):
    body = {
        "xpus": 512,
        "bw_per_xpu_tbps": 25.6,
        "lane_gbps": 200,
        "ferrule_fibers": 16,
        "claimed_fibers_before": 130000,
        "claimed_fiber_saved_miles": [200, 150],
        "claimed_connectors_saved": [16000, 20000],
    }
    r = client.post("/pod", json=body).json()
    assert r["duplex_fibers"] == 131072
    assert r["mean_length_m"][0] == pytest.approx(4.9113, abs=5e-5)
    assert r["connectors_per_mating_plane"] == 4096
    assert client.post("/pod", json={**body, "xpus": 0}).status_code == 422


def test_ring_invalid_is_422(client):
    assert client.post("/ring", json={"q_loaded": 0}).status_code == 422
    assert client.post("/ring", json={"q_loaded": 3500}).status_code == 422  # no FSR or n_g + D


@pytest.mark.parametrize(
    "hypothesis, fsr_ghz, channel, leakage",
    [("H_fsr18", 1800.0, 3, 0.081869), ("H_fsr32", 3200.0, 7, 0.021508)],
)
def test_spectrum_bidi16_from_the_catalog(client, hypothesis, fsr_ghz, channel, leakage):
    # model card §14.5: worst receive channel and its co-directional leakage per hypothesis
    view = client.get("/spectrum/bidi16", params={"hypothesis": hypothesis}).json()
    assert (view["hypothesis"], view["fsr_ghz"], view["q_loaded"]) == (hypothesis, fsr_ghz, 3500.0)
    assert view["accuracy_ghz"] == 20.0
    worst = view["crosstalk"]["worst"]
    assert worst["channel"] == channel
    assert worst["leakage"] == pytest.approx(leakage, abs=5e-7)
    assert view["crosstalk"]["receive_channels"] == [1, 3, 5, 7, 9, 11, 13, 15]
    assert len(view["crosstalk"]["spectra"]) == 8
    assert len(view["crosstalk"]["frequency_ghz"]) == 1601


def test_spectrum_rejects_unknown_hypothesis(client):
    assert client.get("/spectrum/bidi16", params={"hypothesis": "H_fsr99"}).status_code == 422


def test_ptc_simulate(client):
    body = client.post("/ptc/simulate", json={"config": {"gain": 4.0}}).json()
    assert body["label"].startswith("SYNTHETIC inputs (seeded)")
    exact, bf16 = body["hand_cases"]
    # model card §15.3 hand cases
    assert exact["codes"] == [16, -63, 3, 47] and exact["scale"] == 1.2
    assert bf16["scale"] == 1.203125
    assert bf16["max_abs_error"] == pytest.approx(0.007292, abs=5e-7)
    low = client.post("/ptc/simulate", json={"config": {"gain": 1.0}}).json()
    assert body["relative_error"] < low["relative_error"]
    again = client.post("/ptc/simulate", json={"config": {"gain": 4.0}}).content
    assert client.post("/ptc/simulate", json={"config": {"gain": 4.0}}).content == again
    for bad in ({"config": {"gain": 0}}, {"length": 0}, {"config": {"output_range": "2"}}):
        assert client.post("/ptc/simulate", json=bad).status_code == 422
