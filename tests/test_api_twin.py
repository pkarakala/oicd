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
    assert body["independence"].startswith("Independent model built from public information.")
    ids = {p["id"] for p in body["products"]}
    assert {"bidi_engine", "photonic_interposer", "reference_rack", "photonic_processor"} <= ids
    engine = next(p for p in body["products"] if p["id"] == "bidi_engine")
    assert engine["verified_facts"] <= engine["facts"]
    assert {h["id"] for h in engine["hypotheses"]} == {"H_engine_one_dir", "H_engine_both_dirs"}
    assert engine["has_physics"] and engine["has_geometry"]


def test_product_view(client):
    view = client.get("/catalog/bidi_engine").json()
    energy = node(view, "engine.energy_per_bit")
    assert energy["nominal"] == pytest.approx(4.6875)
    assert (energy["lo"], energy["hi"]) == pytest.approx((2.34375, 4.6875))
    assert energy["derivation"] == "30 W / 6.4 Tbps = 4.6875 pJ/bit"
    assert energy["source_class"] == "inference"
    assert node(view, "engine.tdp_max")["quote"] == "TDP (max): 30W"
    assert check(view, "engine.check_energy_bw")["status"] == "TENSION"
    assert check(view, "engine.check_widths")["status"] == "CONFLICT"
    assert [r["hypothesis"] for r in view["graph"]["support"]] == [
        "baseline",
        "H_engine_one_dir",
        "H_engine_both_dirs",
    ]
    assert any(t["node"] == "engine.energy_per_bit" and t["bars"] for t in view["graph"]["tornado"])
    assert view["physics"]["sections"][0]["verdict"] == "EXCLUDED"


def test_inference_with_hypothesis_and_override(client):
    both = client.post("/inference/bidi_engine", json={"hypotheses": ["H_engine_both_dirs"]}).json()
    assert node(both, "engine.energy_per_bit")["nominal"] == pytest.approx(2.34375)
    assert node(both, "engine.energy_direction_factor")["pinned_by"] == "H_engine_both_dirs"
    wide = client.post(
        "/inference/bidi_engine", json={"overrides": {"engine.lambda_tolerance_nm": 6.5}}
    ).json()
    assert node(wide, "engine.a_upper_edge")["nominal"] == pytest.approx(1317.5)
    assert check(wide, "engine.check_a_upper")["status"] == "CONSISTENT"


@pytest.mark.parametrize(
    "body",
    [
        {"hypotheses": ["H_nope"]},
        {"hypotheses": ["H_engine_one_dir", "H_engine_both_dirs"]},
        {"overrides": {"engine.tdp_max": 10.0}},
        {"overrides": {"no.such": 1.0}},
    ],
    ids=["unknown-hypothesis", "alternatives", "override-a-fact", "unknown-override"],
)
def test_inference_invalid_is_422(client, body):
    assert client.post("/inference/bidi_engine", json=body).status_code == 422


def test_unknown_product_is_404(client):
    assert client.get("/catalog/no_such_product").status_code == 404
    assert client.post("/inference/no_such_product", json={}).status_code == 404


def test_catalog_json_is_deterministic(client):
    assert (
        client.get("/catalog/bidi_16lambda").content == client.get("/catalog/bidi_16lambda").content
    )


def test_geometry(client):
    listing = client.get("/geometry").json()
    assert "bidi_engine" in listing["scenes"]
    assert [i["id"] for i in listing["info"]] == listing["scenes"]
    ring = listing["info"][listing["scenes"].index("ring_section")]
    assert (ring["unit"], ring["parent"], ring["breadcrumb"]) == ("nm", "pic_region", "Ring")
    scene = client.get("/geometry/bidi_engine").json()
    assert scene["source_issues"] == []
    outline = next(p for p in scene["scene"]["part"] if p["id"] == "eng.outline")
    assert outline["size"] == [37.5, 27.6, 4.55]
    assert outline["dims_class"] == "VENDOR"
    assert {p["dims_class"] for p in scene["scene"]["part"]} == {"VENDOR", "SCHEMATIC"}
    for bad in ("no_such_scene", "..%2Fpyproject", "Bidi_Engine"):
        assert client.get(f"/geometry/{bad}").status_code == 404


def test_geometry_serves_evaluated_nodes_and_captions(client):
    scene = client.get("/geometry/bidi_engine").json()
    nodes = {n["id"]: n for n in scene["nodes"]}
    # the Inspector shows both package widths: the conflict stays visible
    assert nodes["engine.width_mm_yole"]["nominal"] == 27.6
    assert nodes["engine.width_mm_web"]["nominal"] == 26.4
    assert nodes["engine.energy_per_bit"]["derivation"] == "30 W / 6.4 Tbps = 4.6875 pJ/bit"
    captions = scene["captions"]
    assert len(captions) == len(scene["scene"]["tour"]) == 8
    energy = next(c for c in captions if c["ref"] == "engine.energy_per_bit")
    assert energy == {
        "part": "eng.eic",
        "ref": "engine.energy_per_bit",
        "text": "energy per bit at maximum TDP: 30 W / 6.4 Tbps = 4.6875 pJ/bit",
        "badge": "inference",
    }
    link = client.get("/geometry/bidi_link").json()
    b_upper = next(c for c in link["captions"] if c["ref"] == "engine.check_b_upper")
    assert b_upper["badge"] == "TENSION"
    assert b_upper["text"].startswith("1331 nm ≤ 1317.5 nm (max) fails → TENSION, gap 13.5 nm.")
    assert [c["id"] for c in link["checks"]] == ["engine.check_b_upper"]
    assert link["checks"][0]["gap_abs"] == pytest.approx(13.5)
