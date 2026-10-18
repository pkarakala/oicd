"""Twin formulas (model card §14): each unit-tested against hand values."""

import math

import pytest

from oicd.twin import formulas as f
from oicd.twin.formulas import FORMULAS, format_number, render, resolve_out_unit


@pytest.mark.parametrize(
    "name, args, expected",
    [
        ("pj_per_bit", (30.0, 6.4), 4.6875),  # §14 L20: 30 W / 6.4 Tbps
        ("pj_per_bit", (30.0, 12.8), 2.34375),
        ("power_w_at_pj_per_bit", (3.0, 6.4), 19.2),
        ("lanes", (204.8, 200.0), 1024.0),
        ("rate_per_unit_gbps", (6.4, 32.0), 200.0),
        ("aggregate_tbps", (256.0, 448.0), 114.688),
        ("times_count", (8.0, 56.0), 448.0),
        ("divide_by_count", (204.8, 8.0), 25.6),
        ("count_ratio", (32.0, 8.0), 4.0),
        ("ratio", (212.5, 200.0), 1.0625),
        ("reduction_fraction", (32.0, 64.0), 0.5),
        ("sum2", (12.8, 65.0), 77.8),
        ("difference", (1331.0, 1311.0), 20.0),
        ("total_w_from_mw", (64.0, 200.0), 12.8),
        ("dbm_difference_db", (24.5, 23.0103), 1.4897),
        ("kw_to_w", (1.5,), 1500.0),
        ("area_mm2", (91.0, 85.0), 7735.0),
        ("volume_mm3", (37.5, 27.6, 4.55), 4709.25),
        ("power_density_w_per_mm2", (1500.0, 4000.0), 0.375),
        ("power_w_from_density", (4000.0, 1.4), 5600.0),
        ("miles_to_m", (200.0,), 321868.8),
        ("ops_tops", (65536.0, 500.0), 65.536),
        ("tops_per_w", (65.536, 78.0), 0.840205),
        ("heater_power_mw", (1.1449, 0.44), 2.602045),
    ],
)
def test_formula_values(name, args, expected):
    assert FORMULAS[name].fn(*args) == pytest.approx(expected, rel=1e-6)


def test_frequency_and_spacing():
    # §14 L20: 1311 and 1331 nm are 20 nm = 3436.1 GHz apart; f0 at 1310 nm = 228.8492 THz.
    assert f.nm_pair_spacing_ghz(1311.0, 1331.0) == pytest.approx(3436.1, abs=0.05)
    assert f.frequency_ghz_from_nm(1310.0) == pytest.approx(228849.2, abs=0.05)
    assert f.ghz_span_to_nm(20.0, 1310.0) == pytest.approx(0.11449, abs=5e-6)


def test_mw_to_dbm():
    assert f.mw_to_dbm(200.0) == pytest.approx(23.0103, abs=5e-5)
    assert f.mw_to_dbm(13.0) == pytest.approx(11.1394, abs=5e-5)
    with pytest.raises(ValueError):
        f.mw_to_dbm(0.0)


def test_units_resolve():
    assert resolve_out_unit(FORMULAS["pj_per_bit"], ("W", "Tbps")) == "pJ/bit"
    assert resolve_out_unit(FORMULAS["times_count"], ("count", "Gbps")) == "Gbps"
    assert resolve_out_unit(FORMULAS["ratio"], ("mm", "mm")) == "1"
    with pytest.raises(ValueError, match="must be in W"):
        resolve_out_unit(FORMULAS["pj_per_bit"], ("mW", "Tbps"))
    with pytest.raises(ValueError, match="must match"):
        resolve_out_unit(FORMULAS["ratio"], ("mm", "nm"))
    with pytest.raises(ValueError, match="takes 2 inputs"):
        resolve_out_unit(FORMULAS["ratio"], ("mm",))


def test_render_and_format():
    text = render(FORMULAS["pj_per_bit"], (30.0, 6.4), ("W", "Tbps"))
    assert text == "30 W / 6.4 Tbps"
    assert render(FORMULAS["count_ratio"], (32.0, 8.0), ("count", "count")) == "32 / 8"
    assert format_number(263.7824) == "263.782"
    assert format_number(131072.0) == "131072"


def test_formulas_are_pure_functions_of_floats():
    for formula in FORMULAS.values():
        assert callable(formula.fn)
        assert all(isinstance(p, str) and isinstance(u, str) for p, u in formula.params)
        assert formula.name == formula.fn.__name__
        assert not math.isnan(len(formula.template))
