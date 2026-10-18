"""Twin endpoints: /catalog, /catalog/{product}, /inference/{product}, /geometry. Expected values
from model card §14."""

import pytest
from fastapi.testclient import TestClient

from oicd.api import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def node(view, node_id):
    return next(n for n in view["graph"]["nodes"] if n["id"] == node_id)


def check(view, check_id):
    return next(c for c in view["graph"]["checks"] if c["id"] == check_id)


def test_catalog_index(client):
    body = client.get("/catalog").json()
    assert body["independence"].startswith("Independent reconstruction from public information.")
    ids = {p["id"] for p in body["products"]}
    assert {"passage_l20", "passage_m1000", "reference_rack", "photonic_processor"} <= ids
    l20 = next(p for p in body["products"] if p["id"] == "passage_l20")
    assert l20["verified_facts"] <= l20["facts"]
    assert {h["id"] for h in l20["hypotheses"]} == {"H_l20_one_dir", "H_l20_both_dirs"}
    assert l20["has_physics"] and l20["has_geometry"]


def test_product_view(client):
    view = client.get("/catalog/passage_l20").json()
    energy = node(view, "l20.energy_per_bit")
    assert energy["nominal"] == pytest.approx(4.6875)
    assert (energy["lo"], energy["hi"]) == pytest.approx((2.34375, 4.6875))
    assert energy["derivation"] == "30 W / 6.4 Tbps = 4.6875 pJ/bit"
    assert energy["source_class"] == "inference"
    assert node(view, "l20.tdp_max")["quote"] == "TDP (max): 30W"
    assert check(view, "l20.check_energy_bw")["status"] == "TENSION"
    assert check(view, "l20.check_widths")["status"] == "CONFLICT"
    assert [r["hypothesis"] for r in view["graph"]["support"]] == [
        "baseline",
        "H_l20_one_dir",
        "H_l20_both_dirs",
    ]
    assert any(t["node"] == "l20.energy_per_bit" and t["bars"] for t in view["graph"]["tornado"])
    assert view["physics"]["sections"][0]["verdict"] == "EXCLUDED"


def test_inference_with_hypothesis_and_override(client):
    both = client.post("/inference/passage_l20", json={"hypotheses": ["H_l20_both_dirs"]}).json()
    assert node(both, "l20.energy_per_bit")["nominal"] == pytest.approx(2.34375)
    assert node(both, "l20.energy_direction_factor")["pinned_by"] == "H_l20_both_dirs"
    wide = client.post(
        "/inference/passage_l20", json={"overrides": {"l20.lambda_tolerance_nm": 6.5}}
    ).json()
    assert node(wide, "l20.a_upper_edge")["nominal"] == pytest.approx(1317.5)
    assert check(wide, "l20.check_a_upper")["status"] == "CONSISTENT"


@pytest.mark.parametrize(
    "body",
    [
        {"hypotheses": ["H_nope"]},
        {"hypotheses": ["H_l20_one_dir", "H_l20_both_dirs"]},
        {"overrides": {"l20.tdp_max": 10.0}},
        {"overrides": {"no.such": 1.0}},
    ],
    ids=["unknown-hypothesis", "alternatives", "override-a-fact", "unknown-override"],
)
def test_inference_invalid_is_422(client, body):
    assert client.post("/inference/passage_l20", json=body).status_code == 422


def test_unknown_product_is_404(client):
    assert client.get("/catalog/no_such_product").status_code == 404
    assert client.post("/inference/no_such_product", json={}).status_code == 404


def test_catalog_json_is_deterministic(client):
    assert (
        client.get("/catalog/bidi_16lambda").content == client.get("/catalog/bidi_16lambda").content
    )


def test_geometry(client):
    assert "passage_l20" in client.get("/geometry").json()["scenes"]
    scene = client.get("/geometry/passage_l20").json()
    assert scene["source_issues"] == []
    outline = next(p for p in scene["scene"]["part"] if p["id"] == "l20g.outline")
    assert outline["size"] == [37.5, 27.6, 4.55]
    assert outline["dims_class"] == "VENDOR"
    assert {p["dims_class"] for p in scene["scene"]["part"]} == {"VENDOR", "SCHEMATIC"}
    for bad in ("no_such_scene", "..%2Fpyproject", "Passage_L20"):
        assert client.get(f"/geometry/{bad}").status_code == 404
