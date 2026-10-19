"""Geometry scene format (catalog/geometry/*.toml): dims_class, sizes and instancing."""

import tomllib
from pathlib import Path

import pytest

from oicd.twin.catalog import (
    GEOMETRY_DIR,
    GeometryScene,
    geometry_path,
    load_catalog,
    load_geometry,
    validate_geometry_sources,
)

GEOMETRY_TOY = Path(__file__).parent / "data" / "geometry_toy"
CATALOG_TOY = Path(__file__).parent / "data" / "catalog_toy"


def test_toy_scene_loads_and_sources_resolve():
    scene = load_geometry("toy_engine", GEOMETRY_TOY)
    assert scene.scene.unit == "mm"
    assert [p.dims_class for p in scene.part] == ["VENDOR", "SCHEMATIC", "SCHEMATIC"]
    catalog = load_catalog(CATALOG_TOY, citation_keys=frozenset({"toy_source", "toy_other"}))
    assert validate_geometry_sources(scene, catalog) == []


def test_unknown_dims_source_is_reported():
    data = tomllib.loads((GEOMETRY_TOY / "toy_engine.toml").read_text(encoding="utf-8"))
    data["part"][0]["dims_source"] = "toy.nothing"
    scene = GeometryScene.model_validate(data)
    catalog = load_catalog(CATALOG_TOY, citation_keys=frozenset({"toy_source", "toy_other"}))
    assert validate_geometry_sources(scene, catalog) == [
        "toy.package: dims_source 'toy.nothing' is not a catalog node"
    ]


def test_unverified_dims_source_is_reported():
    scene = load_geometry("toy_engine", GEOMETRY_TOY)
    catalog = load_catalog(CATALOG_TOY, citation_keys=frozenset({"toy_source", "toy_other"}))
    sourced = next(p for p in scene.part if p.sourced)
    fact = catalog.nodes[sourced.dims_source]
    nodes = {**catalog.nodes, fact.id: fact.model_copy(update={"verified": False})}
    issues = validate_geometry_sources(scene, catalog.model_copy(update={"nodes": nodes}))
    assert issues == [f"{sourced.id}: dims_axes claim a source but {fact.id!r} is unverified"]


@pytest.mark.parametrize(
    "change, message",
    [
        ({"size": [0.0, 1.0, 1.0]}, "positive"),
        ({"count": 5}, "does not hold count"),
        ({"dims_class": "GUESS"}, "dims_class"),
        ({"dims_source": " "}, "dims_source"),
        ({"shape": "tube"}, "path"),
        ({"shape": "ring"}, "needs a wall"),
        ({"wall": 0.1}, "only a ring"),
        ({"shape": "ring", "size": [1.0, 1.0, 0.2], "wall": 0.5}, "under its radius"),
        ({"dims_class": "VENDOR", "dims_axes": ["VENDOR", "SCHEMATIC", "VENDOR"]}, "weakest"),
    ],
)
def test_part_rules(change, message):
    data = tomllib.loads((GEOMETRY_TOY / "toy_engine.toml").read_text(encoding="utf-8"))
    data["part"][2].update(change)
    with pytest.raises(ValueError, match=message):
        GeometryScene.model_validate(data)


def test_scene_names_cannot_escape_the_directory():
    for bad in ("../toy", "toy_engine.toml", "", "Toy"):
        with pytest.raises(FileNotFoundError):
            geometry_path(bad, GEOMETRY_TOY)


def test_dims_axes_name_the_weakest_axis():
    data = tomllib.loads((GEOMETRY_TOY / "toy_engine.toml").read_text(encoding="utf-8"))
    data["part"][0].update(dims_class="SCHEMATIC", dims_axes=["VENDOR", "VENDOR", "SCHEMATIC"])
    part = GeometryScene.model_validate(data).part[0]
    assert part.dims_class == "SCHEMATIC" and part.sourced
    data["part"][0].update(dims_axes=["SCHEMATIC", "SCHEMATIC", "SCHEMATIC"])
    assert not GeometryScene.model_validate(data).part[0].sourced


@pytest.mark.parametrize(
    "stop, message",
    [
        ({"part": "toy.die"}, "node or a caption"),
        ({"part": "toy.die", "caption": "  "}, "node or a caption"),
        ({"part": "toy.lid", "caption": "a lid"}, "unknown part"),
    ],
)
def test_tour_rules(stop, message):
    data = tomllib.loads((GEOMETRY_TOY / "toy_engine.toml").read_text(encoding="utf-8"))
    data["tour"] = [stop]
    with pytest.raises(ValueError, match=message):
        GeometryScene.model_validate(data)


def test_unknown_tour_node_part_node_and_product_are_reported():
    data = tomllib.loads((GEOMETRY_TOY / "toy_engine.toml").read_text(encoding="utf-8"))
    data["scene"]["product"] = "toy_missing"
    data["part"][1]["nodes"] = ["toy.nothing"]
    data["tour"] = [{"part": "toy.die", "node": "toy.nowhere"}]
    scene = GeometryScene.model_validate(data)
    catalog = load_catalog(CATALOG_TOY, citation_keys=frozenset({"toy_source", "toy_other"}))
    assert validate_geometry_sources(scene, catalog) == [
        "tour stop at toy.die: node 'toy.nowhere' is not in the catalog",
        "toy.die: node 'toy.nothing' is not in the catalog",
        "product 'toy_missing' is not a catalog file",
    ]


SCENES = sorted(p.stem for p in GEOMETRY_DIR.glob("*.toml"))


def test_shipped_scenes():
    assert SCENES == [
        "bidi_engine",
        "bidi_link",
        "cpo_chiplet",
        "laser_sources",
        "photonic_interposer",
        "photonic_processor",
        "pic_region",
        "reference_rack",
        "ring_section",
        "switch_tray",
        "xpu_tray",
    ]
    catalog = load_catalog()
    for name in SCENES:
        scene = load_geometry(name)
        assert scene.scene.id == name
        assert validate_geometry_sources(scene, catalog) == [], name
        assert 5 <= len(scene.tour) <= 8, name
        # every shipped caption comes from the catalog, so it carries a class or a status
        assert all(t.node for t in scene.tour), name
        assert scene.scene.product in catalog.files, name
        for part in scene.part:
            assert part.enters in ("", *SCENES), (name, part.id)
        assert scene.scene.parent in ("", *SCENES), name


def test_semantic_zoom_chain_from_ring_to_rack():
    # Rack (m) > Tray (cm) > Engine (mm) > PIC (um) > Ring (nm), each scene in its own unit
    chain, name = [], "ring_section"
    while name:
        scene = load_geometry(name)
        chain.append((scene.scene.breadcrumb, scene.scene.unit, scene.scene.level))
        name = scene.scene.parent
    assert chain[::-1] == [
        ("Rack", "mm", "rack"),
        ("Switch tray", "mm", "tray"),
        ("Engine", "mm", "package"),
        ("PIC", "um", "pic"),
        ("Ring", "nm", "device"),
    ]
    rack = load_geometry("reference_rack")
    assert {p.enters for p in rack.part if p.enters} == {"switch_tray", "xpu_tray"}


def test_engine_outline_and_lnic_classes():
    engine = {p.id: p for p in load_geometry("bidi_engine").part}
    outline = engine["eng.outline"]
    assert outline.size == (37.5, 27.6, 4.55) and outline.dims_axes == ("VENDOR",) * 3
    assert "engine.width_mm_web" in outline.nodes  # the 26.4 mm conflict is one click away
    lnic = {p.id: p for p in load_geometry("laser_sources").part}["elsdr.pcb"]
    # depth 115 mm is published for both OCP NIC 3.0 sizes; the 76 mm width is our SFF reading
    assert lnic.size[:2] == (76.0, 115.0)
    assert lnic.dims_axes == ("INFERENCE", "PUBLISHED", "SCHEMATIC")
    ring = {p.id: p for p in load_geometry("pic_region").part}["pic.mrm"]
    assert ring.shape == "ring" and ring.size[:2] == (15.0, 15.0)
    assert ring.dims_axes == ("INFERENCE", "INFERENCE", "SCHEMATIC")
