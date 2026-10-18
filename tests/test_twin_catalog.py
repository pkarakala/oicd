"""Twin catalog validation (model card §14.1). Catalog errors surface as ValueError (Pydantic's
ValidationError wraps the CatalogError raised by the whole-catalog validator)."""

import tomllib
from pathlib import Path

import pytest

from oicd.twin.catalog import Catalog, CatalogFile, load_catalog

TOY_DIR = Path(__file__).parent / "data" / "catalog_toy"
TOY_KEYS = frozenset({"toy_source", "toy_other"})


def toy_files() -> dict[str, dict]:
    return {p.stem: tomllib.loads(p.read_text(encoding="utf-8")) for p in TOY_DIR.glob("*.toml")}


def build(files: dict[str, dict]) -> Catalog:
    return Catalog.model_validate(
        {"files": {k: CatalogFile.model_validate(v) for k, v in files.items()}},
        context={"citation_keys": TOY_KEYS},
    )


def test_toy_catalog_loads():
    catalog = load_catalog(TOY_DIR, citation_keys=TOY_KEYS)
    assert set(catalog.files) == {"toy", "toysum"}
    assert catalog.owner["toy.energy"] == "toy"
    assert "H_two_directions" in catalog.hypotheses


def test_unknown_citation_is_rejected():
    with pytest.raises(ValueError, match="not in references.bib"):
        load_catalog(TOY_DIR, citation_keys=frozenset({"toy_source"}))


def test_duplicate_ids_are_rejected():
    files = toy_files()
    files["toy"]["fact"].append(dict(files["toy"]["fact"][0]))
    with pytest.raises(ValueError, match="duplicate id"):
        build(files)


def test_unresolved_input_is_rejected():
    files = toy_files()
    files["toy"]["derived"][0]["inputs"] = ["toy.direction_factor", "toy.no_such_node"]
    with pytest.raises(ValueError, match="unknown node"):
        build(files)


def test_cycle_is_rejected():
    files = toy_files()
    files["toy"]["derived"][0]["inputs"] = ["toy.direction_factor", "toy.energy"]
    files["toy"]["derived"][0]["fn"] = "times_count"
    files["toy"]["derived"][1]["inputs"] = ["toy.power", "toy.rate_counted"]
    # toy.rate_counted -> toy.energy -> toy.rate_counted; units now disagree too.
    with pytest.raises(ValueError, match="cycle"):
        build(files)


def test_unit_mismatch_is_rejected():
    files = toy_files()
    files["toy"]["derived"][1]["inputs"] = ["toy.per_lambda", "toy.rate_counted"]  # mW, not W
    with pytest.raises(ValueError, match="must be in W"):
        build(files)


def test_declared_unit_must_match_formula():
    files = toy_files()
    files["toy"]["derived"][1]["unit"] = "W"
    with pytest.raises(ValueError, match="gives pJ/bit"):
        build(files)


def test_bound_check_needs_a_min_or_max_fact():
    files = toy_files()
    files["toy"]["check"][3]["b"] = "toy.per_lambda"
    with pytest.raises(ValueError, match="min or max fact or a relation"):
        build(files)
    files["toy"]["check"][3]["relation"] = "ge"  # an explicit relation makes it valid
    assert build(files).checks["toy.check_fiber_power"].relation == "ge"
    files["toy"]["check"][0]["relation"] = "le"
    with pytest.raises(ValueError, match="bound checks only"):
        build(files)


def test_hypothesis_must_pin_an_assumption_inside_its_range():
    files = toy_files()
    files["toy"]["hypothesis"][1]["sets"] = {"toy.direction_factor": 3.0}
    with pytest.raises(ValueError, match="outside"):
        build(files)
    files["toy"]["hypothesis"][1]["sets"] = {"toy.power": 1.0}
    with pytest.raises(ValueError, match="not an assumption"):
        build(files)


def test_text_fact_cannot_feed_a_formula():
    files = toy_files()
    files["toy"]["derived"][2]["inputs"] = ["toy.modulation", "toy.per_lambda"]
    with pytest.raises(ValueError, match="has no number"):
        build(files)


@pytest.mark.parametrize(
    "change, message",
    [
        ({"source_class": "synthetic"}, "must be cited"),
        ({"lo": 1.0, "hi": 2.0}, "not both"),
        ({"verified": False}, "needs a note"),
        ({"quote": "  "}, "blank"),
    ],
)
def test_fact_rules(change, message):
    files = toy_files()
    files["toy"]["fact"][0].update(change)
    with pytest.raises(ValueError, match=message):
        build(files)


def test_unknown_formula_is_rejected():
    files = toy_files()
    files["toy"]["derived"][0]["fn"] = "eval"
    with pytest.raises(ValueError, match="unknown formula"):
        build(files)
