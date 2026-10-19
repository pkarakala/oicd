"""HTTP API: the worked example over the wire, invalid input and unknown profiles."""

import json

import pytest
from fastapi.testclient import TestClient

from oicd.api import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="module")
def worked_example_json(client) -> dict:
    response = client.get("/profiles/worked_example")
    assert response.status_code == 200
    return response.json()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_evaluate_worked_example(client, worked_example_json):
    # Model card §4: M_net = +0.4992 dB, PASS.
    response = client.post("/evaluate", json=worked_example_json)
    assert response.status_code == 200
    report = response.json()
    assert report["margin_db"] == pytest.approx(0.4992, abs=1e-9)
    assert report["verdict"] == "NOT_EXCLUDED"
    assert report["power_trace"][-1]["power_dbm"] == pytest.approx(-4.0008, abs=1e-9)


def test_evaluate_negative_loss_is_422(client, worked_example_json):
    bad = json.loads(json.dumps(worked_example_json))
    bad["channel"][0]["loss_max"]["value"]["value"] = -0.5
    response = client.post("/evaluate", json=bad)
    assert response.status_code == 422
    assert "loss_max must be >= 0.0" in response.json()["detail"]


def test_evaluate_average_power_is_422(client, worked_example_json):
    # T07: a unit-kind mismatch is invalid input, not a FAIL verdict.
    bad = json.loads(json.dumps(worked_example_json))
    bad["tx"]["launch_oma_min"]["value"]["kind"] = "average"
    response = client.post("/evaluate", json=bad)
    assert response.status_code == 422
    assert "must be OMA" in response.json()["detail"]


def test_unknown_profile_is_404(client):
    assert client.get("/profiles/no_such_profile").status_code == 404


def test_cors_allows_only_vite_dev_origin(client):
    preflight = {"Access-Control-Request-Method": "POST"}
    ok = client.options("/evaluate", headers={"Origin": "http://localhost:5173", **preflight})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    other = client.options("/evaluate", headers={"Origin": "http://evil.example", **preflight})
    assert "access-control-allow-origin" not in other.headers


def _with_chain_json(link_json: dict, chain_json: dict) -> dict:
    data = json.loads(json.dumps(link_json))
    data["tx"]["launch_oma_min"] = None
    data["tx"]["upstream"] = chain_json
    return data


def test_profiles_list(client):
    response = client.get("/profiles")
    assert response.status_code == 200
    assert "worked_example" in response.json()["profiles"]


def test_sweep_hand_cases(client, worked_example_json):
    # Model card §8: (1.0, 0) -> +0.4992; (2.0, 0) -> -0.5008; (0, +1) -> +2.4992.
    body = {
        "link": worked_example_json,
        "x": {"path": "channel[2].loss_max", "start": 0.0, "stop": 2.0, "num": 21},
        "y": {"path": "tx.launch_oma_min", "start": -1.0, "stop": 1.0, "num": 21},
    }
    response = client.post("/sweep", json=body)
    assert response.status_code == 200
    result = response.json()
    xs, ys, m = result["x"]["values"], result["y"]["values"], result["margin_db"]
    assert m[ys.index(0.0)][xs.index(1.0)] == pytest.approx(0.4992, abs=1e-9)
    assert m[ys.index(0.0)][xs.index(2.0)] == pytest.approx(-0.5008, abs=1e-9)
    assert m[ys.index(1.0)][xs.index(0.0)] == pytest.approx(2.4992, abs=1e-9)
    assert client.post("/sweep", json=body).content == response.content


@pytest.mark.parametrize(
    "x",
    [
        {"path": "no.such.input", "values": [0.0, 1.0]},
        {"path": "channel[2].loss_max", "start": 0.0, "stop": 2.0, "num": 202},
        {"path": "channel[2].loss_max", "values": [float(v) for v in range(202)]},
        {"path": "channel[2].loss_max", "values": [-1.0, 0.0]},
        {"path": "channel[2].loss_max"},
    ],
    ids=["unknown-path", "oversized-range", "oversized-values", "invalid-physics", "no-values"],
)
def test_sweep_invalid_is_422(client, worked_example_json, x):
    body = {"link": worked_example_json, "x": x, "y": {"path": "reserve", "values": [1.5]}}
    response = client.post("/sweep", json=body)
    assert response.status_code == 422
    assert response.json()["detail"]


def test_evaluate_tray_hand_case(client, worked_example_json):
    # Model card §9: lane 5 patch connector 2.0 dB -> -0.5008 dB, deciding lane 5, EXCLUDED.
    lanes = [json.loads(json.dumps(worked_example_json)) for _ in range(8)]
    lanes[5]["channel"][2]["loss_max"]["value"]["value"] = 2.0
    response = client.post("/evaluate_tray", json={"name": "8-lane tray", "lanes": lanes})
    assert response.status_code == 200
    tray = response.json()
    assert tray["verdict"] == "EXCLUDED"
    assert tray["deciding_lane"] == 5
    assert tray["margin_db"] == pytest.approx(-0.5008, abs=1e-9)


def test_evaluate_tray_empty_is_422(client):
    assert client.post("/evaluate_tray", json={"lanes": []}).status_code == 422


def test_evaluate_with_upstream_chain(client, worked_example_json):
    # Model card §10: N = 16 -> M +0.3081 dB NOT_EXCLUDED; max fan-out 17.
    def q(value, unit_value=True):
        provenance = {"source_class": "synthetic", "citation_key": None, "rationale": "§10 case"}
        return {"value": {"value": value} if unit_value else value, "provenance": provenance}

    chain = {
        "laser_power_avg": q({"power_dbm": {"value": 20.0}, "kind": "average"}, False),
        "laser_fiber_loss": q(0.5),
        "coupling_loss": q(1.5),
        "split_n": q(16, False),
        "excess_loss": q(0.0),
        "modulator_il": q(4.0),
        "output_coupler_loss": q(1.5),
        "extinction_ratio": q(4.0),
    }
    response = client.post("/evaluate", json=_with_chain_json(worked_example_json, chain))
    assert response.status_code == 200
    report = response.json()
    assert report["margin_db"] == pytest.approx(0.3081, abs=1e-4)
    assert report["verdict"] == "NOT_EXCLUDED"
    assert report["upstream"]["max_fanout"] == 17
    chain["laser_power_avg"]["value"]["kind"] = "oma"
    bad = client.post("/evaluate", json=_with_chain_json(worked_example_json, chain))
    assert bad.status_code == 422
    assert "AVERAGE" in bad.json()["detail"]


def test_yield_hand_case(client, worked_example_json):
    # Model card §11: yield 0.92522; the worst-case verdict is reported unchanged.
    link = json.loads(json.dumps(worked_example_json))
    provenance = {"source_class": "synthetic", "citation_key": None, "rationale": "§11 case"}
    for i in (0, 2, 4):
        mean = link["channel"][i]["loss_max"]["value"]["value"]
        link["channel"][i]["loss_distribution"] = {
            "mean": {"value": {"value": mean}, "provenance": provenance},
            "sigma": {"value": {"value": 0.2}, "provenance": provenance},
        }
    response = client.post("/yield", json={"link": link, "n_samples": 200_000, "seed": 1})
    assert response.status_code == 200
    body = response.json()
    assert body["label"] == "statistical, assumption-dependent"
    assert body["worst_case_verdict"] == "NOT_EXCLUDED"
    assert body["analytic"]["yield_fraction"] == pytest.approx(0.92522, abs=1e-5)
    assert body["monte_carlo"]["yield_fraction"] == pytest.approx(0.92522, abs=0.005)
    too_many = client.post("/yield", json={"link": link, "n_samples": 1_000_001})
    assert too_many.status_code == 422


def test_responses_are_canonical_json(client, worked_example_json):
    text = client.post("/evaluate", json=worked_example_json).text
    assert text == json.dumps(
        json.loads(text), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def test_references_list_every_bib_entry_with_its_link(client):
    entries = {e["key"]: e for e in client.get("/references").json()["entries"]}
    from oicd.provenance import load_citation_keys

    assert set(entries) == load_citation_keys()
    g652 = entries["itut_g652_2024"]
    assert g652["url"].startswith("https://") and g652["title"]
    assert "{" not in "".join(e["title"] for e in entries.values())
