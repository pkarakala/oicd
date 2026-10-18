"""Geometry scene format (catalog/geometry/*.toml): dims_class, sizes and instancing."""

import tomllib
from pathlib import Path

import pytest

from oicd.twin.catalog import (
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


@pytest.mark.parametrize(
    "change, message",
    [
        ({"size": [0.0, 1.0, 1.0]}, "positive"),
        ({"count": 5}, "does not hold count"),
        ({"dims_class": "GUESS"}, "dims_class"),
        ({"dims_source": " "}, "dims_source"),
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
