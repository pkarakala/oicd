"""Inference engine on the toy graph (model card §14.1 hand case)."""

from pathlib import Path

import pytest

from oicd.provenance import SourceClass
from oicd.twin.catalog import CatalogError, load_catalog
from oicd.twin.inference import CORNER_LIMIT, evaluate_graph

TOY_DIR = Path(__file__).parent / "data" / "catalog_toy"


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(TOY_DIR, citation_keys=frozenset({"toy_source", "toy_other"}))


@pytest.fixture(scope="module")
def graph(catalog):
    return evaluate_graph(catalog, "toy")


def node(graph, node_id):
    return next(n for n in graph.nodes if n.id == node_id)


def check(graph, check_id):
    return next(c for c in graph.checks if c.id == check_id)


def test_energy_nominal_interval_and_derivation(graph):
    # §14.1: 4.6875 pJ/bit at factor 1; corners over factor 1 to 2 give 2.34375 to 4.6875.
    energy = node(graph, "toy.energy")
    assert energy.nominal == pytest.approx(4.6875, abs=1e-12)
    assert (energy.lo, energy.hi) == pytest.approx((2.34375, 4.6875), abs=1e-12)
    assert energy.method == "corners"
    assert energy.interval_parents == ("toy.direction_factor",)
    assert energy.source_class is SourceClass.INFERENCE
    assert energy.derivation == "30 W / 6.4 Tbps = 4.6875 pJ/bit"


def test_classes_of_every_node(graph):
    assert node(graph, "toy.power").source_class is SourceClass.VENDOR_CLAIM
    assert node(graph, "toy.direction_factor").source_class is SourceClass.SYNTHETIC
    assert node(graph, "toy.power").quote == "TDP (max): 30W"
    assert node(graph, "toy.energy_copy").verified is False


def test_check_statuses(graph):
    # §14.1: 6.25% within 10% -> CONSISTENT; 56.25% -> TENSION (derived); widths -> CONFLICT.
    c5 = check(graph, "toy.check_5pj")
    assert (c5.status, c5.gap_rel) == ("CONSISTENT", pytest.approx(0.0625))
    c3 = check(graph, "toy.check_3pj")
    assert (c3.status, c3.gap_rel) == ("TENSION", pytest.approx(0.5625))
    # The energy interval 2.34375 to 4.6875 pJ/bit contains 3.0: a factor inside its range
    # (1.5625) would reconcile the copy, so the intervals overlap.
    assert c3.interval_overlap is True
    widths = check(graph, "toy.check_widths")
    assert (widths.status, widths.gap_rel) == ("CONFLICT", pytest.approx(0.0434782608))
    assert widths.interval_overlap is False  # two points 1.2 mm apart, tolerance 0.276 mm
    bound = check(graph, "toy.check_fiber_power")
    assert bound.status == "CONSISTENT"
    assert bound.a_value == 104.0
    assert "104 mW ≥ 100 mW (min) holds" in bound.explanation


def test_support_matrix(graph):
    # §14.1: under factor 2 the 5 pJ/bit check is TENSION (53.125%), the 3.0 copy CONSISTENT.
    rows = {r.hypothesis: r for r in graph.support}
    assert list(rows) == ["baseline", "H_one_direction", "H_two_directions"]
    two = rows["H_two_directions"]
    assert two.cells["toy.check_5pj"].status == "TENSION"
    assert two.cells["toy.check_5pj"].gap_rel == pytest.approx(0.53125)
    assert two.cells["toy.check_3pj"].status == "CONSISTENT"
    assert two.cells["toy.check_3pj"].gap_rel == pytest.approx(0.21875)
    assert "toy.check_3pj" in two.agrees and "toy.check_5pj" in two.disagrees
    assert rows["H_one_direction"].cells["toy.check_5pj"].status == "CONSISTENT"
    assert rows["baseline"].cells["toy.check_widths"].status == "CONFLICT"


def test_tornado(graph):
    # §14.1: the factor moves the energy by 2.34375 pJ/bit between its low and high.
    entry = next(t for t in graph.tornado if t.node == "toy.energy")
    assert [b.assumption for b in entry.bars] == ["toy.direction_factor"]
    bar = entry.bars[0]
    assert (bar.value_at_low, bar.value_at_high) == pytest.approx((4.6875, 2.34375))
    assert bar.swing == pytest.approx(2.34375)


def test_conflicts_list_both_sources(graph):
    pairs = {(c.a, c.b): c for c in graph.conflicts}
    widths = pairs[("toy.width_a", "toy.width_b")]
    assert (widths.quote_a, widths.quote_b) == ("37.5 mm x 26.4 mm", "37.5 x 27.6 x 4.55mm")
    assert (widths.cite_a, widths.cite_b) == ("toy_source", "toy_other")
    assert ("toy.modulation", "toy.modulation_page") in pairs


def test_hypothesis_choice_pins_the_assumption(catalog):
    graph = evaluate_graph(catalog, "toy", hypotheses=("H_two_directions",))
    energy = node(graph, "toy.energy")
    assert (energy.nominal, energy.lo, energy.hi) == pytest.approx((2.34375,) * 3)
    assert energy.method == "point"
    assert node(graph, "toy.direction_factor").pinned_by == "H_two_directions"


def test_override_pins_and_alternatives_are_exclusive(catalog):
    graph = evaluate_graph(catalog, "toy", overrides={"toy.direction_factor": 1.5})
    assert node(graph, "toy.energy").nominal == pytest.approx(30.0 / 9.6)
    with pytest.raises(CatalogError, match="alternatives"):
        evaluate_graph(catalog, "toy", hypotheses=("H_one_direction", "H_two_directions"))
    with pytest.raises(KeyError):
        evaluate_graph(catalog, "toy", overrides={"toy.power": 10.0})
    with pytest.raises(KeyError):
        evaluate_graph(catalog, "no_such_product")


def test_monte_carlo_above_the_corner_limit(catalog):
    # §14.1: more than 12 interval ancestors -> 4096 seeded samples, flagged.
    graph = evaluate_graph(catalog, "toysum")
    total = node(graph, "toysum.s12")
    assert len(total.interval_parents) == 13 > CORNER_LIMIT
    assert total.method == "monte_carlo" and total.flagged
    assert total.nominal == pytest.approx(13.0)
    assert 6.5 <= total.lo < 13.0 < total.hi <= 19.5
    s11 = node(graph, "toysum.s11")
    assert s11.method == "corners" and not s11.flagged


def test_evaluation_is_deterministic(catalog):
    assert evaluate_graph(catalog, "toysum") == evaluate_graph(catalog, "toysum")
    assert evaluate_graph(catalog) == evaluate_graph(catalog)
