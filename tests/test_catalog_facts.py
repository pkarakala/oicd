"""The shipped catalog (catalog/products/*.toml): structure, provenance and a few Appendix A
values that the brief and the model card rely on."""

import pytest

from oicd.provenance import load_citation_keys
from oicd.twin.catalog import APPENDIX_KEY, Fact, load_catalog, load_unopened_keys


@pytest.fixture(scope="module")
def catalog():
    return load_catalog()


def all_facts(catalog) -> list[Fact]:
    return [f for cf in catalog.files.values() for f in cf.fact]


def test_catalog_loads_with_every_product(catalog):
    assert {
        "passage_m1000",
        "passage_l200",
        "passage_l20",
        "vclick",
        "bidi_16lambda",
        "microring_ofc25",
        "guide_family",
        "ocp_trays",
        "scaleup_pod",
        "standards_partners",
        "photonic_processor",
        "lightmatter_platform",
    } <= set(catalog.files)


def test_verified_facts_cite_opened_sources(catalog):
    keys = load_citation_keys()
    unopened = load_unopened_keys()
    for fact in all_facts(catalog):
        if fact.verified:
            assert fact.cite in keys, fact.id
            assert fact.cite not in unopened, fact.id
        else:
            assert fact.cite in keys | unopened | {APPENDIX_KEY}, fact.id
            assert fact.note.strip(), fact.id


def test_conflicts_point_at_facts(catalog):
    for fact in all_facts(catalog):
        for other in fact.conflicts_with:
            assert isinstance(catalog.nodes[other], Fact)


@pytest.mark.parametrize(
    "fact_id, value",
    [
        ("l20.bw_per_direction", 6.4),
        ("l20.tdp_max", 30.0),
        ("l20.energy_per_bit_bw", 3.0),
        ("l20.energy_per_bit_web", 5.0),
        ("l20.lambda_a_nm", 1311.0),
        ("l20.lambda_b_nm", 1331.0),
        ("m1000.fiber_count", 256.0),
        ("m1000.bw_per_fiber", 448.0),
        ("m1000.bw_per_fiber_ises25", 800.0),
        ("m1000.package_area", 7735.0),
        ("ring.fsr_thz", 1.8),
        ("ring.heater_nm_per_mw", 0.44),
        ("ring.mrm_q", 3500.0),
        ("ring.oma_min_dbm", -9.0),
        ("guidedr.power_per_fiber", 200.0),
        ("guidedr.lanes", 256.0),
        ("trays.switch_bw", 204.8),
        ("trays.xpu_bw", 102.4),
        ("orv3.meta_frame_height", 2286.0),
        ("orv3.meta_capacity_openu", 44.0),
        ("orv3.shelf_height", 46.2),
        ("elsfp.hazard_l1_limit", 24.5),
        ("ieee3dj.channel_il", 3.0),
        ("ptc.throughput_sustained", 65.5),
    ],
)
def test_appendix_values(catalog, fact_id, value):
    fact = catalog.nodes[fact_id]
    assert isinstance(fact, Fact)
    assert fact.value == value


def test_known_conflicts_are_recorded(catalog):
    # Appendix A and the fact check: both sides carried, never silently picked (brief rule 3).
    pairs = {
        ("l20.width_mm_web", "l20.width_mm_yole"),
        ("l20.form_factor_pins", "l20.bga_balls_web"),
        ("m1000.bw_per_fiber", "m1000.bw_per_fiber_ises25"),
        ("l200.l200_lane_rate", "l200.web_modulation"),
        ("trays.xpu_height_prnewswire", "trays.xpu_height_lmcom"),
        ("ptc.c262_web", "ptc.c262_paper"),
    }
    for a, b in pairs:
        assert b in catalog.nodes[a].conflicts_with


def test_unverified_facts_keep_their_reason(catalog):
    unverified = [f for f in all_facts(catalog) if not f.verified]
    assert {f.id for f in unverified} >= {
        "prizm.beam_diameter",
        "ptc.ptc_power_each",
        "ieee3dj.revcom",
    }
    for fact in unverified:
        assert fact.note.startswith("Evidence: none")
