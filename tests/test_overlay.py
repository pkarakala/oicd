"""Scene overlays (oicd.twin.overlay, GET /overlay/{scene}). Expected values from the model card:
§13.8 (BiDi link case), §13.4 and §14.3 (heaters), §14.6 (lasers), §14.9 (reference rack)."""

import pytest
from fastapi.testclient import TestClient

from oicd.api import app
from oicd.display import margin_color
from oicd.twin.catalog import GEOMETRY_DIR, load_catalog, load_geometry
from oicd.twin.overlay import UNDISCLOSED_BRIGHTNESS, OverlayError, overlay_for

CATALOG = load_catalog()
SCENES = sorted(p.stem for p in GEOMETRY_DIR.glob("*.toml"))


def overlay(scene: str, **kwargs):
    return overlay_for(CATALOG, load_geometry(scene), **kwargs)


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


@pytest.mark.parametrize("scene", SCENES)
def test_overlays_name_real_parts_and_stay_on_their_paths(scene):
    o = overlay(scene)
    assert o is not None and o.scene == scene
    parts = {p.id: p for p in load_geometry(scene).part}
    for path in o.paths:
        part = parts[path.part]
        assert part.shape in ("tube", "cylinder"), path.part
        assert all(0 <= i < part.count for i in path.instances)
        assert all(0.0 <= s.at <= 1.0 and s.brightness >= 0.0 for s in path.samples)
        if path.direction != "none":
            ats = [s.at for s in path.samples]
            assert ats == sorted(ats, reverse=path.direction == "backward"), path.label
        if path.power_kind is None:
            # undisclosed power: no number, the fixed display brightness
            assert all(s.power_mw is None for s in path.samples)
            assert all(s.brightness == UNDISCLOSED_BRIGHTNESS for s in path.samples)
    for value in o.values:
        assert value.part in parts
        if value.margin_db is not None:
            assert value.color == margin_color(value.margin_db, o.mode)


def test_bidi_link_case():
    o = overlay("bidi_link")
    assert o.verdict == "EXCLUDED"
    assert o.margin_db == pytest.approx(0.49955, abs=5e-6)
    a, b, ghost_a, ghost_b = o.paths
    assert (a.direction, b.direction) == ("forward", "backward")
    assert a.color != b.color
    # §13.8: launch 2.4 dBm = 1.737801 mW (brightness 1), TP3 0.933254 mW
    assert o.reference_mw == pytest.approx(1.737801, abs=1e-6)
    assert a.samples[0].brightness == pytest.approx(1.0)
    assert a.samples[-1].power_mw == pytest.approx(0.933254, abs=1e-6)
    assert a.samples[-1].brightness == pytest.approx(0.933254 / 1.737801, abs=1e-6)
    # ghosts: the reflected local TX, 1.548817e-4 mW, in the local transmitter's color
    for ghost, color in ((ghost_a, a.color), (ghost_b, b.color)):
        assert ghost.kind == "ghost" and ghost.color == color
        assert ghost.samples[0].power_mw == pytest.approx(1.548817e-4, rel=1e-6)
    received = {v.part: v for v in o.values}
    assert received["link.engine_b"].verdict == "NOT_EXCLUDED"
    assert received["link.engine_a"].verdict == "EXCLUDED"
    assert "wavelength containment fails" in received["link.engine_a"].label
    assert o.verdict_note == "direction B (1331 nm): wavelength containment fails"


def test_bidi_link_ghost_grows_without_isolation():
    o = overlay("bidi_link", isolation_db=0.0)
    assert o.paths[2].samples[0].power_mw == pytest.approx(0.048978, abs=1e-6)
    with pytest.raises(OverlayError):
        overlay("bidi_link", isolation_db=61.0)


@pytest.mark.parametrize(
    "case, margin, verdict",
    [
        ("H_fau_channel_1p5", -1.0016, "EXCLUDED"),
        ("H_fau_channel_1p0", -0.0016, "EXCLUDED"),
        ("H_fau_module", 1.9984, "NOT_EXCLUDED"),
    ],
)
def test_rack_reference_plane_cases(case, margin, verdict):
    for scene in ("reference_rack", "switch_tray", "xpu_tray"):
        o = overlay(scene, case=case)
        assert [c.id for c in o.cases] == [
            "H_fau_channel_1p5",
            "H_fau_channel_1p0",
            "H_fau_module",
        ]
        assert o.case == case and o.verdict == verdict
        assert o.margin_db == pytest.approx(margin, abs=1e-9)
        assert all(v.verdict == verdict for v in o.values)


def test_rack_default_case_and_unknown_case():
    assert overlay("reference_rack").case == "H_fau_channel_1p5"
    with pytest.raises(OverlayError, match="unknown case"):
        overlay("reference_rack", case="H_nowhere")


def test_heaters_and_lasers():
    # §13.4: one 200 GHz spacing 2.6020 mW, a full 1.8 THz FSR 23.4176 mW at 0.44 nm/mW
    for scene, part in (("pic_region", "pic.mrm_heater"), ("ring_section", "rs.heater")):
        heater = next(v for v in overlay(scene).values if v.part == part)
        assert heater.power_mw == pytest.approx(2.6020, abs=5e-5)
        assert heater.intensity == pytest.approx(2.6020 / 23.4176, abs=1e-5)
    lasers = overlay("laser_sources")
    assert lasers.reference_mw == 200.0 and lasers.reference_kind == "AVERAGE"
    # §14.6: ELS-DWDM 8 × 13 mW = 104 mW, ELS-DWDM00 mW, both against the ELS-DR's 200 mW
    assert [p.samples[0].brightness for p in lasers.paths] == pytest.approx([1.0, 0.52, 0.5])
    assert lasers.values[0].power_mw == pytest.approx(12800.0)


def test_processor_overlay():
    o = overlay("photonic_processor")
    assert o.reference_mw == 200.0 and o.reference_kind == "AVERAGE"
    cell = o.values[0]
    # §15.5: 9.6971 µW per cell under H_lasers_dedicated
    assert cell.power_mw == pytest.approx(9.6971e-3, abs=1e-7)


def test_overlay_endpoint(client):
    rack = client.get("/overlay/reference_rack").json()
    assert rack["verdict"] == "EXCLUDED" and rack["case"] == "H_fau_channel_1p5"
    flipped = client.get("/overlay/reference_rack", params={"case": "H_fau_module"}).json()
    assert flipped["verdict"] == "NOT_EXCLUDED"
    assert flipped["margin_db"] == pytest.approx(1.9984, abs=1e-9)
    dark = client.get("/overlay/reference_rack", params={"mode": "dark"}).json()
    assert dark["mode"] == "dark"
    assert client.get("/overlay/reference_rack", params={"case": "H_x"}).status_code == 422
    assert client.get("/overlay/bidi_link", params={"isolation_db": 99}).status_code == 422
    assert client.get("/overlay/no_such_scene").status_code == 404
    first = client.get("/overlay/bidi_link").content
    assert client.get("/overlay/bidi_link").content == first
