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
