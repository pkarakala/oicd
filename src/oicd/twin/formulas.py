"""Formulas for the twin's derived nodes (model card §14).

Each formula is a pure function of floats with units in its parameter names, registered with the
unit of every parameter, the unit of its result and a template for the derivation string, e.g.
"30 W / 6.4 Tbps = 4.6875 pJ/bit". Catalog files name a formula by its key in FORMULAS; nothing
is ever evaluated from a string.

Unit specs: a concrete unit ("W"), or "any:T" for any unit that every "any:T" parameter of the
same formula shares; the result may be "any:T". "1" is dimensionless, "count" a pure number.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass

# Speed of light in vacuum, exact (SI definition); the same constant as oicd.units.
C_M_PER_S = 299_792_458
METERS_PER_MILE = 1609.344  # international mile, exact by definition (1959)


def pj_per_bit(power_w: float, rate_tbps: float) -> float:
    """Energy per bit: W / Tbps = pJ/bit."""
    return power_w / rate_tbps


def power_w_at_pj_per_bit(energy_pj_per_bit: float, rate_tbps: float) -> float:
    """Power for an energy per bit at a rate: pJ/bit × Tbps = W."""
    return energy_pj_per_bit * rate_tbps


def lanes(rate_tbps: float, lane_gbps: float) -> float:
    """Number of lanes that carry rate_tbps at lane_gbps each."""
    return rate_tbps * 1000.0 / lane_gbps


def rate_per_unit_gbps(rate_tbps: float, count: float) -> float:
    """Rate per unit (port, fiber, lane) when rate_tbps is shared by count units."""
    return rate_tbps * 1000.0 / count


def aggregate_tbps(count: float, rate_gbps: float) -> float:
    """Aggregate rate of count units at rate_gbps each."""
    return count * rate_gbps / 1000.0


def times_count(count: float, x: float) -> float:
    """count copies of x (same unit as x)."""
    return count * x


def divide_by_count(x: float, count: float) -> float:
    """x shared equally by count units (same unit as x)."""
    return x / count


def count_ratio(numerator_count: float, denominator_count: float) -> float:
    """Ratio of two counts, e.g. lanes per laser fiber."""
    return numerator_count / denominator_count


def ratio(a: float, b: float) -> float:
    """a / b for two quantities in the same unit (dimensionless)."""
    return a / b


def reduction_fraction(new: float, old: float) -> float:
    """1 − new/old, the fraction saved going from old to new (same unit)."""
    return 1.0 - new / old


def sum2(a: float, b: float) -> float:
    return a + b


def difference(a: float, b: float) -> float:
    """a − b in the same unit."""
    return a - b


def total_w_from_mw(count: float, each_mw: float) -> float:
    """count × each_mw, in W."""
    return count * each_mw / 1000.0


def mw_to_dbm(power_mw: float) -> float:
    if power_mw <= 0.0:
        raise ValueError(f"power must be positive to express in dBm, got {power_mw} mW")
    return 10.0 * math.log10(power_mw)


def dbm_difference_db(a_dbm: float, b_dbm: float) -> float:
    """a − b for two absolute levels: dBm − dBm = dB."""
    return a_dbm - b_dbm


def kw_to_w(power_kw: float) -> float:
    return power_kw * 1000.0


def area_mm2(length_mm: float, width_mm: float) -> float:
    return length_mm * width_mm


def volume_mm3(length_mm: float, width_mm: float, height_mm: float) -> float:
    return length_mm * width_mm * height_mm


def power_density_w_per_mm2(power_w: float, area_mm2: float) -> float:
    return power_w / area_mm2


def power_w_from_density(area_mm2: float, density_w_per_mm2: float) -> float:
    return area_mm2 * density_w_per_mm2


def frequency_ghz_from_nm(wavelength_nm: float) -> float:
    """f = c/λ in GHz."""
    return C_M_PER_S / (wavelength_nm * 1e-9) / 1e9


def nm_pair_spacing_ghz(lambda_a_nm: float, lambda_b_nm: float) -> float:
    """|c/λa − c/λb| in GHz."""
    return abs(frequency_ghz_from_nm(lambda_a_nm) - frequency_ghz_from_nm(lambda_b_nm))


def ghz_span_to_nm(span_ghz: float, wavelength_nm: float) -> float:
    """Δλ ≈ λ²·Δf/c (model card §3)."""
    return (wavelength_nm * 1e-9) ** 2 * (span_ghz * 1e9) / C_M_PER_S * 1e9


def miles_to_m(distance_miles: float) -> float:
    return distance_miles * METERS_PER_MILE


def ops_tops(macs_per_cycle: float, clock_mhz: float) -> float:
    """Operations per second, 2 operations (multiply and add) per MAC, in tera-ops/s."""
    return 2.0 * macs_per_cycle * clock_mhz * 1e6 / 1e12


def tops_per_w(rate_tops: float, power_w: float) -> float:
    return rate_tops / power_w


def heater_power_mw(tuning_nm: float, efficiency_nm_per_mw: float) -> float:
    """Heater power for a thermal tuning range at a tuning efficiency (Δλ = η·P)."""
    return tuning_nm / efficiency_nm_per_mw


@dataclass(frozen=True, slots=True)
class Formula:
    name: str
    fn: Callable[..., float]
    params: tuple[tuple[str, str], ...]  # (parameter name, unit spec)
    out_unit: str
    template: str  # uses {parameter name}


def _f(fn: Callable[..., float], params: tuple[tuple[str, str], ...], out: str, template: str):
    return Formula(fn.__name__, fn, params, out, template)


FORMULAS: dict[str, Formula] = {
    f.name: f
    for f in (
        _f(
            pj_per_bit,
            (("power_w", "W"), ("rate_tbps", "Tbps")),
            "pJ/bit",
            "{power_w} / {rate_tbps}",
        ),
        _f(
            power_w_at_pj_per_bit,
            (("energy_pj_per_bit", "pJ/bit"), ("rate_tbps", "Tbps")),
            "W",
            "{energy_pj_per_bit} × {rate_tbps}",
        ),
        _f(
            lanes,
            (("rate_tbps", "Tbps"), ("lane_gbps", "Gbps")),
            "count",
            "{rate_tbps} / {lane_gbps}",
        ),
        _f(
            rate_per_unit_gbps,
            (("rate_tbps", "Tbps"), ("count", "count")),
            "Gbps",
            "{rate_tbps} / {count}",
        ),
        _f(
            aggregate_tbps,
            (("count", "count"), ("rate_gbps", "Gbps")),
            "Tbps",
            "{count} × {rate_gbps}",
        ),
        _f(times_count, (("count", "count"), ("x", "any:T")), "any:T", "{count} × {x}"),
        _f(divide_by_count, (("x", "any:T"), ("count", "count")), "any:T", "{x} / {count}"),
        _f(
            count_ratio,
            (("numerator_count", "count"), ("denominator_count", "count")),
            "count",
            "{numerator_count} / {denominator_count}",
        ),
        _f(ratio, (("a", "any:T"), ("b", "any:T")), "1", "{a} / {b}"),
        _f(reduction_fraction, (("new", "any:T"), ("old", "any:T")), "1", "1 − {new} / {old}"),
        _f(sum2, (("a", "any:T"), ("b", "any:T")), "any:T", "{a} + {b}"),
        _f(difference, (("a", "any:T"), ("b", "any:T")), "any:T", "{a} − {b}"),
        _f(total_w_from_mw, (("count", "count"), ("each_mw", "mW")), "W", "{count} × {each_mw}"),
        _f(mw_to_dbm, (("power_mw", "mW"),), "dBm", "10·log10({power_mw})"),
        _f(dbm_difference_db, (("a_dbm", "dBm"), ("b_dbm", "dBm")), "dB", "{a_dbm} − {b_dbm}"),
        _f(kw_to_w, (("power_kw", "kW"),), "W", "{power_kw}"),
        _f(area_mm2, (("length_mm", "mm"), ("width_mm", "mm")), "mm2", "{length_mm} × {width_mm}"),
        _f(
            volume_mm3,
            (("length_mm", "mm"), ("width_mm", "mm"), ("height_mm", "mm")),
            "mm3",
            "{length_mm} × {width_mm} × {height_mm}",
        ),
        _f(
            power_density_w_per_mm2,
            (("power_w", "W"), ("area_mm2", "mm2")),
            "W/mm2",
            "{power_w} / {area_mm2}",
        ),
        _f(
            power_w_from_density,
            (("area_mm2", "mm2"), ("density_w_per_mm2", "W/mm2")),
            "W",
            "{area_mm2} × {density_w_per_mm2}",
        ),
        _f(frequency_ghz_from_nm, (("wavelength_nm", "nm"),), "GHz", "c / {wavelength_nm}"),
        _f(
            nm_pair_spacing_ghz,
            (("lambda_a_nm", "nm"), ("lambda_b_nm", "nm")),
            "GHz",
            "|c/{lambda_a_nm} − c/{lambda_b_nm}|",
        ),
        _f(
            ghz_span_to_nm,
            (("span_ghz", "GHz"), ("wavelength_nm", "nm")),
            "nm",
            "{wavelength_nm}² × {span_ghz} / c",
        ),
        _f(miles_to_m, (("distance_miles", "miles"),), "m", "{distance_miles} × 1609.344 m/mile"),
        _f(
            ops_tops,
            (("macs_per_cycle", "count"), ("clock_mhz", "MHz")),
            "TOPS",
            "2 × {macs_per_cycle} × {clock_mhz}",
        ),
        _f(
            tops_per_w,
            (("rate_tops", "TOPS"), ("power_w", "W")),
            "TOPS/W",
            "{rate_tops} / {power_w}",
        ),
        _f(
            heater_power_mw,
            (("tuning_nm", "nm"), ("efficiency_nm_per_mw", "nm/mW")),
            "mW",
            "{tuning_nm} / {efficiency_nm_per_mw}",
        ),
    )
}


def resolve_out_unit(formula: Formula, input_units: tuple[str, ...]) -> str:
    """The result unit for these input units; ValueError if they do not fit the formula."""
    if len(input_units) != len(formula.params):
        raise ValueError(
            f"{formula.name} takes {len(formula.params)} inputs, got {len(input_units)}"
        )
    bound: dict[str, str] = {}
    for (param, spec), unit in zip(formula.params, input_units, strict=True):
        if spec.startswith("any:"):
            if bound.setdefault(spec, unit) != unit:
                raise ValueError(
                    f"{formula.name}: {param} is in {unit} but must match {bound[spec]}"
                )
        elif spec != unit:
            raise ValueError(f"{formula.name}: {param} must be in {spec}, got {unit}")
    if formula.out_unit.startswith("any:"):
        return bound[formula.out_unit]
    return formula.out_unit


def format_number(x: float) -> str:
    """Six significant digits, no trailing zeros: 4.6875, 263.782, 131072."""
    return f"{x:.6g}"


def with_unit(x: float, unit: str) -> str:
    return format_number(x) if unit in ("1", "count") else f"{format_number(x)} {unit}"


def render(formula: Formula, values: tuple[float, ...], units: tuple[str, ...]) -> str:
    """The template filled with values and units, e.g. "30 W / 6.4 Tbps"."""
    names = [p for p, _ in formula.params]
    return formula.template.format(
        **{n: with_unit(v, u) for n, v, u in zip(names, values, units, strict=True)}
    )
