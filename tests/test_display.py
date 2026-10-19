"""oicd.display and GET /display: every color the explorer shows is decided by the engine."""

import pytest
from fastapi.testclient import TestClient

from oicd.api import app
from oicd.display import BLUE, MATERIALS, ORANGE, RED, channel_colors, margin_color, palette
from oicd.provenance import SourceClass
from oicd.twin.catalog import GEOMETRY_DIR, load_geometry


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_every_source_class_has_one_labelled_color(mode):
    p = palette(mode)
    assert {s.key for s in p.classes} == {c.value for c in SourceClass}
    assert all(s.label for s in p.classes)
    colors = [s.color for s in p.classes]
    assert len(set(colors)) == len(colors)


def test_synthetic_and_schematic_are_gray():
    p = palette("light")
    by_key = {s.key: s.color for s in p.classes}
    dims = {s.key: s.color for s in p.dims_classes}
    assert by_key["synthetic"] == dims["SCHEMATIC"] == "#898781"
    assert dims["VENDOR"] == by_key["vendor_claim"]
    assert dims["PUBLISHED"] == by_key["published_spec"]
    assert dims["INFERENCE"] == by_key["inference"]


def test_status_colors_carry_an_icon_and_a_label():
    status = {s.key: s for s in palette().status}
    assert set(status) == {
        "CONSISTENT",
        "TENSION",
        "CONFLICT",
        "NOT_EXCLUDED",
        "EXCLUDED",
        "NOT_EVALUATED",
    }
    assert all(s.icon and s.label for s in status.values())
    assert status["CONSISTENT"].color == status["NOT_EXCLUDED"].color
    assert status["CONFLICT"].color == status["EXCLUDED"].color


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_margin_scale_diverges_about_zero(mode):
    p = palette(mode)
    assert [s.value_db for s in p.margin_scale] == [-3.0, -1.5, 0.0, 1.5, 3.0]
    assert p.margin_range_db == 3.0
    assert [s.color for s in p.margin_scale] == [
        RED[7],
        RED[3],
        p.margin_bins[8].color,
        BLUE[3],
        BLUE[7],
    ]
    # the midpoint is a neutral, never a hue of either pole
    assert p.margin_scale[2].color not in (*RED, *BLUE)


def test_margin_bins_tile_the_line_and_keep_the_verdict_sign():
    bins = palette().margin_bins
    assert len(bins) == 17 and bins[0].lo_db is None and bins[-1].hi_db is None
    assert all(a.hi_db == b.lo_db for a, b in zip(bins, bins[1:], strict=False))
    # T04 / T16: a float margin a few ulps below 0 is NOT_EXCLUDED and shows neutral, a margin
    # just past -epsilon is EXCLUDED and shows red, never the reverse
    assert margin_color(-4.4e-16) == margin_color(0.0) == bins[8].color
    assert margin_color(-2e-9) == RED[0] and margin_color(2e-9) == BLUE[0]
    # the rack's worst paths (model card §14.9)
    assert margin_color(-1.0016) == RED[2]
    assert margin_color(-0.0016) == RED[0]
    assert margin_color(1.9984) == BLUE[4]
    assert margin_color(-40.0) == RED[7] and margin_color(40.0) == BLUE[7]
    with pytest.raises(ValueError):
        margin_color(float("nan"))


def test_channel_hue_follows_direction():
    channels = channel_colors(16)
    assert [c.channel for c in channels] == list(range(16))
    assert all(c.direction == ("A" if c.channel % 2 == 0 else "B") for c in channels)
    assert all(c.color in (BLUE if c.direction == "A" else ORANGE) for c in channels)
    # lightness runs across each direction's channels: first and last steps of each ramp
    assert (channels[0].color, channels[14].color) == (BLUE[0], BLUE[7])
    assert (channels[1].color, channels[15].color) == (ORANGE[0], ORANGE[7])
    # one channel per direction (the L20's 1311 / 1331 nm): the ramps' middle step
    assert [c.color for c in channel_colors(2)] == [BLUE[3], ORANGE[3]]
    assert len(channel_colors(1)) == 1 and channel_colors(2)[1].direction == "B"


def test_edges_are_a_shade_darker():
    from oicd.display import shade

    assert shade("#3d4654", 0.62) == "#262b34"
    silicon = next(m for m in MATERIALS if m.key == "silicon")
    assert silicon.edge == "#262b34"
    assert palette().materials[0].model_dump()["edge"] == silicon.edge


def test_materials_are_unique_and_physical():
    keys = [m.key for m in MATERIALS]
    assert len(keys) == len(set(keys))
    for m in MATERIALS:
        assert 0 <= m.metalness <= 1 and 0 <= m.roughness <= 1
        assert 0 <= m.transmission <= 1 and 0 < m.opacity <= 1 and m.ior >= 1


def test_every_scene_material_is_served():
    keys = {m.key for m in MATERIALS}
    for path in GEOMETRY_DIR.glob("*.toml"):
        assert {p.material for p in load_geometry(path.stem).part} <= keys, path.stem


def test_display_endpoint(client):
    light = client.get("/display").json()
    assert light["mode"] == "light" and len(light["channels"]) == 16
    assert light["channel_legend"].startswith("False color; O-band light is invisible.")
    dark = client.get("/display", params={"mode": "dark", "channels": 8}).json()
    assert dark["mode"] == "dark" and len(dark["channels"]) == 8
    assert dark["surface"] != light["surface"]
    assert client.get("/display").content == client.get("/display").content
    for params in ({"channels": 0}, {"channels": 129}, {"mode": "sepia"}):
        assert client.get("/display", params=params).status_code == 422
