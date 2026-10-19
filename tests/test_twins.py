"""Model card §14: product twins and the reference rack. Expected values are copied from §14.2 to
§14.9 (and through them from the brief), never from running the code."""

import pytest

from oicd.twin.catalog import load_catalog
from oicd.twin.inference import evaluate_graph
from oicd.twin.physics import physics_for

T = 1e-4  # four-decimal card values


@pytest.fixture(scope="module")
def catalog():
    return load_catalog()


def graph(catalog, product, *hypotheses):
    return evaluate_graph(catalog, product, hypotheses=tuple(hypotheses))


def nominal(g, node_id):
    return next(n for n in g.nodes if n.id == node_id).nominal


def status(g, check_id):
    return next(c for c in g.checks if c.id == check_id).status


def item(physics, title_part, label_part, hypothesis=None):
    for section in physics.sections:
        if title_part in section.title and (hypothesis is None or section.hypothesis == hypothesis):
            for it in section.items:
                if label_part in it.label:
                    return it.value
    raise KeyError((title_part, label_part))


# ---- §14.2 Passage L20 ------------------------------------------------------------------------


def test_l20_values(catalog):
    g = graph(catalog, "passage_l20")
    assert nominal(g, "l20.rate_per_port") == pytest.approx(200.0)
    assert nominal(g, "l20.line_payload_ratio") == pytest.approx(1.0625)
    assert nominal(g, "l20.energy_per_bit") == pytest.approx(4.6875)
    assert nominal(g, "l20.energy_per_bit_both") == pytest.approx(2.34375)
    assert nominal(g, "l20.power_for_3pj") == pytest.approx(19.2)
    assert nominal(g, "l20.lambda_spacing_nm") == pytest.approx(20.0)
    assert nominal(g, "l20.lambda_spacing_ghz") == pytest.approx(3436.1, abs=0.05)
    assert nominal(g, "l20.lanes_per_laser_fiber") == pytest.approx(4.0)
    assert nominal(g, "l20.fiber_reduction_pct") == pytest.approx(50.0)
    assert nominal(g, "l20.volume") == pytest.approx(4709.25)
    assert nominal(g, "l20.pluggable_volume") == pytest.approx(38669.15)
    assert nominal(g, "l20.volume_reduction_pct") == pytest.approx(87.82, abs=0.005)
    assert nominal(g, "l20.switch_bw_18") == pytest.approx(115.2)
    assert nominal(g, "l20.xpu_bw_6") == pytest.approx(38.4)
    assert nominal(g, "l20.savings_vs_17_pct") == pytest.approx(70.59, abs=0.005)
    assert nominal(g, "l20.savings_vs_20_pct") == pytest.approx(75.0)


def test_l20_checks(catalog):
    g = graph(catalog, "passage_l20")
    expected = {
        "l20.check_port_rate": "CONSISTENT",
        "l20.check_energy_web": "CONSISTENT",
        "l20.check_energy_yole": "CONSISTENT",
        "l20.check_energy_bw": "TENSION",
        "l20.check_tdp_for_3pj": "TENSION",
        "l20.check_energy_copies": "CONFLICT",
        "l20.check_cwdm_spacing": "CONSISTENT",
        "l20.check_a_lower": "CONSISTENT",
        "l20.check_a_upper": "CONSISTENT",
        "l20.check_b_upper": "TENSION",
        "l20.check_fiber_reduction": "CONSISTENT",
        "l20.check_volume": "CONSISTENT",
        "l20.check_switch_bw": "CONSISTENT",
        "l20.check_xpu_bw": "CONSISTENT",
        "l20.check_savings": "CONSISTENT",
        "l20.check_widths": "CONFLICT",
        "l20.check_pins": "CONFLICT",
    }
    for check_id, want in expected.items():
        assert status(g, check_id) == want, check_id
    rows = {r.hypothesis: r for r in g.support}
    assert "l20.check_energy_web" in rows["H_l20_one_dir"].agrees
    assert "l20.check_energy_web" in rows["H_l20_both_dirs"].disagrees


def test_l20_dr_wavelength_physics(catalog):
    # §14.2: 1311 nm passes with 6.5 nm clearance each side; 1331 nm fails by 13.5 nm.
    p = physics_for(catalog, "passage_l20")
    assert item(p, "DR wavelength", "direction A at 1311 nm: lower") == pytest.approx(6.5)
    assert item(p, "DR wavelength", "direction A at 1311 nm: upper") == pytest.approx(6.5)
    assert item(p, "DR wavelength", "direction B at 1331 nm: upper") == pytest.approx(-13.5)
    assert p.sections[0].verdict == "EXCLUDED"


# ---- §14.3 Passage M1000 ----------------------------------------------------------------------


def test_m1000_values(catalog):
    g = graph(catalog, "passage_m1000")
    assert nominal(g, "m1000.bw_fibers") == pytest.approx(114.688)
    assert nominal(g, "m1000.per_fiber_lambdas") == pytest.approx(448.0)
    assert nominal(g, "m1000.bw_serdes") == pytest.approx(114.688)
    assert nominal(g, "m1000.links_total") == 256.0
    assert nominal(g, "m1000.serdes_total") == 1024.0
    assert nominal(g, "m1000.package_area_dims") == pytest.approx(7735.0)
    assert nominal(g, "m1000.power_ceiling") == pytest.approx(5600.0)
    assert nominal(g, "m1000.density_package") == pytest.approx(0.194, abs=5e-4)
    assert nominal(g, "m1000.density_interposer") == pytest.approx(0.375)
    assert nominal(g, "m1000.lambda_channels") == 2048.0
    assert nominal(g, "m1000.heater_per_ring") == pytest.approx(2.6020, abs=T)
    assert nominal(g, "m1000.heater_total") == pytest.approx(5.329, abs=5e-4)
    for check_id in ("m1000.check_bw_pr", "m1000.check_bw_evk", "m1000.check_serdes_txrx"):
        assert status(g, check_id) == "CONSISTENT"
    assert status(g, "m1000.check_fiber_rate_ises") == "CONFLICT"
    assert status(g, "m1000.check_density_claim") == "TENSION"


@pytest.mark.parametrize(
    "hypothesis, watts, share", [("H_m1000_txrx", 263.78, 17.6), ("H_m1000_per_dir", 131.89, 8.8)]
)
def test_m1000_io_power_hypotheses(catalog, hypothesis, watts, share):
    g = graph(catalog, "passage_m1000", hypothesis)
    assert nominal(g, "m1000.io_power") == pytest.approx(watts, abs=0.005)
    assert nominal(g, "m1000.io_power_share_pct") == pytest.approx(share, abs=0.05)


# ---- §14.4 Passage L200 -----------------------------------------------------------------------


def test_l200_values_and_readings(catalog):
    g = graph(catalog, "passage_l200")
    assert nominal(g, "l200.bw_l200") == pytest.approx(32.0)
    assert nominal(g, "l200.bw_l200x") == pytest.approx(64.0)
    assert nominal(g, "l200.fibers_l200") == pytest.approx(40.0)
    assert nominal(g, "l200.fibers_l200x") == pytest.approx(40.0)
    assert nominal(g, "l200.package_bw") == pytest.approx(256.0)
    assert nominal(g, "l200.per_pluggable") == pytest.approx(800.0)
    rows = {r.hypothesis: r for r in g.support}
    assert {"l200.check_32", "l200.check_64", "l200.check_256"} <= set(
        rows["H_l200_payload"].agrees
    )
    assert {"l200.check_32", "l200.check_64"} <= set(rows["H_l200_line"].disagrees)


# ---- §14.5 16λ BiDi link ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "hypothesis, channel, x, nrz, xr, refl, min_tx",
    [
        ("H_fsr18", 3.0, 0.081869, 0.3710, 1.082941, 0.2729, -5.2059),
        ("H_fsr32", 7.0, 0.021508, 0.0944, 0.064485, 0.0158, -5.7395),
    ],
)
def test_bidi16_worst_channel(catalog, hypothesis, channel, x, nrz, xr, refl, min_tx):
    p = physics_for(catalog, "bidi_16lambda")
    title = "Worst receive channel"
    assert item(p, title, "worst receive channel", hypothesis) == channel
    assert item(p, title, "co-directional leakage", hypothesis) == pytest.approx(x, abs=5e-7)
    assert item(p, title, "crosstalk penalty", hypothesis) == pytest.approx(nrz, abs=T)
    assert item(p, title, "reflected local", hypothesis) == pytest.approx(xr, abs=5e-7)
    assert item(p, title, "reflection crosstalk", hypothesis) == pytest.approx(refl, abs=T)
    assert item(p, title, "MPI bound", hypothesis) == pytest.approx(0.1503, abs=T)
    assert item(p, title, "minimum TX OMA", hypothesis) == pytest.approx(min_tx, abs=T)


def test_bidi16_aliasing_and_interleaving(catalog):
    p = physics_for(catalog, "bidi_16lambda")
    # §14.5: under H_fsr18 seven of eight receive rings (all but channel 7) have an image on a
    # local transmit channel; interleaving gains 5.935 dB of isolation.
    hits = item(p, "Worst receive channel", "image on a local transmitter", "H_fsr18")
    assert hits == "1, 3, 5, 9, 11, 13, 15"
    assert item(p, "Interleaving", "isolation gained") == pytest.approx(5.935, abs=5e-4)


def test_bidi16_hypothesis_support(catalog):
    g = graph(catalog, "bidi_16lambda")
    rows = {r.hypothesis: r for r in g.support}
    assert rows["H_fsr18"].cells["bidi16.check_fsr_ofc25"].status == "CONSISTENT"
    assert rows["H_fsr18"].cells["bidi16.check_unique_channel"].status == "TENSION"
    assert rows["H_fsr32"].cells["bidi16.check_fsr_ofc25"].status == "TENSION"
    assert rows["H_fsr32"].cells["bidi16.check_unique_channel"].status == "CONSISTENT"
    assert nominal(g, "bidi16.bw_per_fiber_calc") == pytest.approx(800.0)
    assert nominal(g, "bidi16.bw_per_dir") == pytest.approx(400.0)


# ---- §14.6 Guide family -----------------------------------------------------------------------


def test_guide_values(catalog):
    g = graph(catalog, "guide_family")
    assert nominal(g, "guide1.fiber_power") == pytest.approx(104.0)
    assert nominal(g, "guide1.single_package_power") == pytest.approx(1.6)
    stacked = next(n for n in g.nodes if n.id == "guide1.stacked_power")
    assert (stacked.lo, stacked.hi) == pytest.approx((3.2, 3.52))
    assert nominal(g, "guide.module_bw_needed") == pytest.approx(25.0)
    assert nominal(g, "guide.bw_per_elsfp") == pytest.approx(5.556, abs=5e-4)
    assert nominal(g, "guidedr.total_power") == pytest.approx(12.8)
    assert nominal(g, "guidedr.bw") == pytest.approx(51.2)
    assert nominal(g, "guidedr.lanes_per_fiber") == pytest.approx(4.0)
    assert nominal(g, "guidedr.power_per_lane_dbm") == pytest.approx(16.99, abs=0.005)
    assert nominal(g, "guidedr.power_dbm") == pytest.approx(23.01, abs=0.005)
    assert nominal(g, "guidedr.hazard_headroom") == pytest.approx(1.49, abs=0.005)
    assert nominal(g, "guide1.lambda_power_dbm") == pytest.approx(11.14, abs=0.005)
    assert nominal(g, "guidedr.margin_n4") == pytest.approx(6.4398, abs=T)
    assert nominal(g, "guidedr.max_fanout") == 17.0
    for check_id in ("guide1.check_fiber_power", "guide.check_module_bw", "guidedr.check_hazard"):
        assert status(g, check_id) == "CONSISTENT"
    assert status(g, "guidedr.check_lasers") == "CONFLICT"


def test_guide_dr_fanout_physics(catalog):
    # §14.6: N = 4: 9.4897 / 8.8398 dBm, +6.4398 dB; N = 17: +0.1559; N = 18: -0.0923; max 17.
    p = physics_for(catalog, "guide_family")
    assert item(p, "Guide DR", "N = 4").startswith(
        "P_TP2,avg 9.4897 dBm, P_TP2,OMA 8.8398 dBm, M +6.4398 dB, NOT_EXCLUDED"
    )
    assert "M +0.1559 dB, NOT_EXCLUDED" in item(p, "Guide DR", "N = 17")
    assert "M -0.0923 dB, EXCLUDED" in item(p, "Guide DR", "N = 18")
    assert item(p, "Guide DR", "max fan-out") == 17.0


# ---- §14.7 OCP trays --------------------------------------------------------------------------


def test_tray_hypotheses(catalog):
    g = graph(catalog, "ocp_trays")
    assert nominal(g, "trays.switch_per_engine") == pytest.approx(25.6)
    assert nominal(g, "trays.engine_in_l20s") == pytest.approx(4.0)
    rows = {r.hypothesis: r for r in g.support}
    assert {"trays.check_guidedr_release", "trays.check_xpu_guidedr_counterpoint"} <= set(
        rows["H_dir"].agrees
    )
    assert {"trays.check_guidedr_counterpoint", "trays.check_ine_aggregate"} <= set(
        rows["H_agg"].agrees
    )
    assert {"trays.check_height_prnewswire", "trays.check_height_futurum"} <= set(
        rows["H_xpu_1u"].agrees
    )
    assert {"trays.check_height_lmcom", "trays.check_height_counterpoint"} <= set(
        rows["H_xpu_2u"].agrees
    )
    h_dir = graph(catalog, "ocp_trays", "H_dir")
    assert nominal(h_dir, "trays.switch_lanes") == 1024.0
    assert nominal(h_dir, "trays.switch_guidedr_needed") == 4.0
    assert nominal(h_dir, "trays.xpu_guidedr_needed") == 2.0
    h_agg = graph(catalog, "ocp_trays", "H_agg")
    assert nominal(h_agg, "trays.switch_lanes") == 512.0
    assert nominal(h_agg, "trays.switch_guidedr_needed") == 2.0


# ---- §14.8 Pod --------------------------------------------------------------------------------


def test_pod(catalog):
    g = graph(catalog, "scaleup_pod")
    assert nominal(g, "pod.duplex_fibers") == 131072.0
    assert nominal(g, "pod.bidi_fibers") == 65536.0
    assert nominal(g, "pod.mean_length_200") == pytest.approx(4.9113, abs=T)
    assert nominal(g, "pod.mean_length_150") == pytest.approx(3.6835, abs=T)
    assert nominal(g, "pod.connectors_per_plane") == 4096.0
    assert nominal(g, "pod.connectors_saved") == 16384.0
    assert status(g, "pod.check_fibers_before") == "CONSISTENT"
    assert status(g, "pod.check_xpu_tray") == "CONSISTENT"
    assert status(g, "pod.check_hoti_bw") == "TENSION"
    assert status(g, "pod.check_connectors_hoti") == "TENSION"
    h32 = graph(catalog, "scaleup_pod", "H_pod_32")
    assert nominal(h32, "pod.duplex_fibers") == 163840.0
    fibers = next(c for c in h32.checks if c.id == "pod.check_fibers_before")
    assert fibers.status == "TENSION" and fibers.gap_rel == pytest.approx(0.26, abs=0.005)


# ---- §14.9 Reference rack ---------------------------------------------------------------------


def test_rack_graph(catalog):
    g = graph(catalog, "reference_rack")
    assert nominal(g, "rack.links") == 8192.0
    assert nominal(g, "rack.duplex_fibers") == 16384.0
    assert nominal(g, "rack.guidedr") == 64.0
    assert nominal(g, "rack.fiber_db") == pytest.approx(0.0016)
    assert nominal(graph(catalog, "reference_rack", "H_2U"), "rack.ou_used") == 42.0
    assert nominal(graph(catalog, "reference_rack", "H_1U"), "rack.ou_used") == 26.0
    channel = graph(catalog, "reference_rack", "H_vclick_channel")
    module = graph(catalog, "reference_rack", "H_vclick_module")
    assert nominal(channel, "rack.margin") == pytest.approx(-1.0016, abs=T)
    assert nominal(module, "rack.margin") == pytest.approx(1.9984, abs=T)
    assert status(channel, "rack.check_margin") == "TENSION"
    assert status(module, "rack.check_margin") == "CONSISTENT"
    assert nominal(g, "rack.single_tier_xpus") == 64.0


def test_rack_physics(catalog):
    p = physics_for(catalog, "reference_rack")
    margins = {
        (s.hypothesis, s.title): (item(p, s.title, "M_net", s.hypothesis), s.verdict)
        for s in p.sections
        if s.title.startswith("Worst path")
    }
    assert sorted((round(m, 4), v) for m, v in margins.values()) == [
        (-1.0016, "EXCLUDED"),
        (-0.0016, "EXCLUDED"),
        (1.9984, "NOT_EXCLUDED"),
    ]
    assert item(p, "Rack yield", "link yield 0.9999") == pytest.approx(0.4408, abs=T)
    assert item(p, "Rack yield", "link yield 0.99999") == pytest.approx(0.9213, abs=T)
    assert item(p, "Rack yield", "99% rack") == pytest.approx(0.99999877, abs=5e-9)
    assert item(p, "Rack yield", "one-sided z") == pytest.approx(4.712, abs=5e-4)
    assert item(p, "Single-tier", "Guide DR modules") == 64.0


def test_every_product_evaluates(catalog):
    for product in catalog.files:
        g = evaluate_graph(catalog, product)
        assert g.scope == product
        assert evaluate_graph(catalog, product) == g  # deterministic


def test_every_physics_evaluation_runs_and_labels_its_numbers():
    from oicd.provenance import SourceClass
    from oicd.twin.catalog import load_catalog
    from oicd.twin.physics import EVALUATIONS, physics_for

    catalog = load_catalog()
    for product in EVALUATIONS:
        physics = physics_for(catalog, product)
        assert physics is not None and physics.sections, product
        for section in physics.sections:
            assert section.title and section.items, (product, section.title)
            assert all(isinstance(i.source_class, SourceClass) for i in section.items)
    assert physics_for(catalog, "vclick") is None
