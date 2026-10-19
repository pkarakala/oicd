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
        "photonic_interposer",
        "cpo_chiplet",
        "bidi_engine",
        "fiber_array_unit",
        "bidi_16lambda",
        "microring_ofc25",
        "laser_sources",
        "ocp_trays",
        "scaleup_pod",
        "standards_partners",
        "photonic_processor",
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
        ("engine.bw_per_direction", 6.4),
        ("engine.tdp_max", 30.0),
        ("engine.energy_per_bit_bw", 3.0),
        ("engine.energy_per_bit_web", 5.0),
        ("engine.lambda_a_nm", 1311.0),
        ("engine.lambda_b_nm", 1331.0),
        ("interposer.fiber_count", 256.0),
        ("interposer.bw_per_fiber", 448.0),
        ("interposer.bw_per_fiber_ises25", 800.0),
        ("interposer.package_area", 7735.0),
        ("ring.fsr_thz", 1.8),
        ("ring.heater_nm_per_mw", 0.44),
        ("ring.mrm_q", 3500.0),
        ("ring.oma_min_dbm", -9.0),
        ("els_dr.power_per_fiber", 200.0),
        ("els_dr.lanes", 256.0),
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
        ("engine.width_mm_web", "engine.width_mm_yole"),
        ("engine.form_factor_pins", "engine.bga_balls_web"),
        ("interposer.bw_per_fiber", "interposer.bw_per_fiber_ises25"),
        ("chiplet.chiplet_lane_rate", "chiplet.web_modulation"),
        ("trays.xpu_height_prnewswire", "trays.xpu_height_vendor_site"),
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
