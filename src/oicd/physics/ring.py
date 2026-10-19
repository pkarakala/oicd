"""Microring relations (model card §13).

f0 = c/λ0;  FSR_f = c/(n_g·L), FSR_λ = λ0²/(n_g·L);  FWHM = f0/Q_L;
drop port T(Δ) = Σ_k 1/(1 + (2(Δ − k·FSR)/FWHM)²), k = −50 … 50;
Δλ = λ0·Δn_eff/n_g (decort2011);  thermal tuning Δλ = η·P;  dλ/dT = λ0·(dn/dT)/n_g.

WDM crosstalk penalty (INFERENCE): Π = −10·log10(1 − k·X), k = 1 NRZ, 3 PAM4, invalid if k·X ≥ 1;
the alternative 10·log10(1 + X) (andre2000_xtalk) is reported alongside.
Design window (SYNTHETIC rules): Q_min = f0·√(10^(−XT/10) − 1)/(2Δ), Q_max = f0/(b·B).
"""

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict

from oicd.units import C_M_PER_S

_FROZEN = ConfigDict(frozen=True, extra="forbid")

IMAGES = 50  # resonance orders summed on each side of the fundamental (§13.1)

Modulation = Literal["NRZ", "PAM4"]
EYE_FACTOR = {"NRZ": 1, "PAM4": 3}  # PAM4's inner eye is OMA/3


def _positive(value: float, name: str) -> float:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0, got {value!r}")
    return float(value)


def resonance_frequency_ghz(wavelength_nm: float) -> float:
    """f0 = c/λ0."""
    return C_M_PER_S / (_positive(wavelength_nm, "wavelength_nm") * 1e-9) / 1e9


def wavelength_nm(frequency_ghz: float) -> float:
    return C_M_PER_S / (_positive(frequency_ghz, "frequency_ghz") * 1e9) * 1e9


def span_nm(span_ghz: float, wavelength_nm: float) -> float:
    """Δλ ≈ λ²·Δf/c (model card §3)."""
    lam = _positive(wavelength_nm, "wavelength_nm") * 1e-9
    return lam**2 * span_ghz * 1e9 / C_M_PER_S * 1e9


def circumference_um(diameter_um: float) -> float:
    return math.pi * _positive(diameter_um, "diameter_um")


def fsr_ghz(group_index: float, length_um: float) -> float:
    """FSR_f = c/(n_g·L)."""
    return (
        C_M_PER_S
        / (_positive(group_index, "group_index") * _positive(length_um, "length_um") * 1e-6)
        / 1e9
    )


def fsr_nm(wavelength_nm: float, group_index: float, length_um: float) -> float:
    """FSR_λ = λ²/(n_g·L)."""
    lam = _positive(wavelength_nm, "wavelength_nm") * 1e-9
    return (
        lam**2
        / (_positive(group_index, "group_index") * _positive(length_um, "length_um") * 1e-6)
        * 1e9
    )


def group_index_from_fsr(fsr_ghz: float, length_um: float) -> float:
    """n_g = c/(FSR_f·L)."""
    return C_M_PER_S / (
        _positive(fsr_ghz, "fsr_ghz") * 1e9 * _positive(length_um, "length_um") * 1e-6
    )


def max_radius_um(group_index: float, fsr_needed_ghz: float) -> float:
    """Largest radius whose FSR is at least fsr_needed: L ≤ c/(n_g·FSR), R = L/(2π)."""
    length_m = C_M_PER_S / (
        _positive(group_index, "group_index") * _positive(fsr_needed_ghz, "fsr_needed_ghz") * 1e9
    )
    return length_m / (2.0 * math.pi) * 1e6


def fwhm_ghz(f0_ghz: float, q_loaded: float) -> float:
    """FWHM = f0/Q_L, also used as the photon-lifetime bandwidth (energy lifetime, §13.1)."""
    return _positive(f0_ghz, "f0_ghz") / _positive(q_loaded, "q_loaded")


def lorentzian(detuning_ghz: float, fwhm_ghz: float) -> float:
    """Single-resonance drop-port power transmission, 1 at resonance."""
    return 1.0 / (1.0 + (2.0 * detuning_ghz / _positive(fwhm_ghz, "fwhm_ghz")) ** 2)


def drop_response(
    detuning_ghz: float, fwhm_ghz: float, fsr_ghz: float, images: int = IMAGES
) -> float:
    """Drop-port transmission periodic in the FSR: images k = −images … images summed."""
    _positive(fsr_ghz, "fsr_ghz")
    return sum(lorentzian(detuning_ghz - k * fsr_ghz, fwhm_ghz) for k in range(-images, images + 1))


def db(ratio: float) -> float:
    return 10.0 * math.log10(_positive(ratio, "ratio"))


class CrosstalkPenalty(BaseModel):
    model_config = _FROZEN

    leakage: float  # X, the summed co-directional leakage (linear)
    modulation: Modulation
    eye_factor: int
    penalty_db: float  # −10·log10(1 − k·X), INFERENCE
    alternative_db: float  # 10·log10(1 + X), andre2000_xtalk (NRZ, adjusted threshold)
    source_class: Literal["inference"] = "inference"


def crosstalk_penalty(leakage: float, modulation: Modulation) -> CrosstalkPenalty:
    """Worst-case eye closure by incoherent leakage X (model card §13.2)."""
    if not math.isfinite(leakage) or leakage < 0.0:
        raise ValueError(f"leakage must be finite and >= 0, got {leakage!r}")
    k = EYE_FACTOR[modulation]
    if k * leakage >= 1.0:
        raise ValueError(f"k·X = {k * leakage} >= 1: the eye is closed (penalty unbounded)")
    return CrosstalkPenalty(
        leakage=leakage,
        modulation=modulation,
        eye_factor=k,
        penalty_db=-10.0 * math.log10(1.0 - k * leakage),
        alternative_db=10.0 * math.log10(1.0 + leakage),
    )


class DesignWindow(BaseModel):
    """[Q_min, Q_max] for one spacing and symbol rate (SYNTHETIC rules, model card §13.3)."""

    model_config = _FROZEN

    f0_ghz: float
    spacing_ghz: float
    symbol_rate_gbd: float
    max_crosstalk_db: float
    bandwidth_factor: float
    q_min: float
    q_max: float
    open: bool
    q: float | None
    q_inside: bool | None


def design_window(
    f0_ghz: float,
    spacing_ghz: float,
    symbol_rate_gbd: float,
    max_crosstalk_db: float = -15.0,
    bandwidth_factor: float = 0.75,
    q: float | None = None,
) -> DesignWindow:
    """Q_min from the per-neighbor crosstalk rule, Q_max from f0/Q ≥ factor × symbol rate."""
    if not math.isfinite(max_crosstalk_db) or max_crosstalk_db >= 0.0:
        raise ValueError(f"max_crosstalk_db must be < 0 dB, got {max_crosstalk_db!r}")
    _positive(spacing_ghz, "spacing_ghz")
    q_min = f0_ghz * math.sqrt(10.0 ** (-max_crosstalk_db / 10.0) - 1.0) / (2.0 * spacing_ghz)
    q_max = _positive(f0_ghz, "f0_ghz") / (
        _positive(bandwidth_factor, "bandwidth_factor")
        * _positive(symbol_rate_gbd, "symbol_rate_gbd")
    )
    return DesignWindow(
        f0_ghz=f0_ghz,
        spacing_ghz=spacing_ghz,
        symbol_rate_gbd=symbol_rate_gbd,
        max_crosstalk_db=max_crosstalk_db,
        bandwidth_factor=bandwidth_factor,
        q_min=q_min,
        q_max=q_max,
        open=q_min <= q_max,
        q=q,
        q_inside=None if q is None else q_min <= q <= q_max,
    )


def heater_power_mw(tuning_nm: float, efficiency_nm_per_mw: float) -> float:
    """P = Δλ/η (Δλ = η·P)."""
    if not math.isfinite(tuning_nm) or tuning_nm < 0.0:
        raise ValueError(f"tuning_nm must be finite and >= 0, got {tuning_nm!r}")
    return tuning_nm / _positive(efficiency_nm_per_mw, "efficiency_nm_per_mw")


def thermal_drift_nm_per_k(wavelength_nm: float, dn_dt_per_k: float, group_index: float) -> float:
    """dλ/dT = λ0·(dn/dT)/n_g, the mode taken fully in silicon (an upper bound, §13.4)."""
    return (
        _positive(wavelength_nm, "wavelength_nm")
        * dn_dt_per_k
        / _positive(group_index, "group_index")
    )


class ThermalTuning(BaseModel):
    """Tuning a ring must cover and the heater power for it (model card §13.4)."""

    model_config = _FROZEN

    laser_accuracy_nm: float
    fabrication_offset_nm: float
    drift_nm: float
    required_nm: float  # sum of the three worst-case offsets
    barrel_shifting: bool
    worst_case_range_nm: float  # one co-directional spacing (barrel shifting) or one FSR
    exceeds_range: bool  # required offsets larger than the worst-case range
    heater_power_mw: float  # power for the worst-case range
    efficiency_nm_per_mw: float


def thermal_tuning(
    wavelength_nm: float,
    laser_accuracy_ghz: float,
    fabrication_offset_nm: float,
    drift_nm_per_k: float,
    temperature_swing_k: float,
    spacing_ghz: float,
    fsr_ghz: float,
    efficiency_nm_per_mw: float,
    barrel_shifting: bool = True,
) -> ThermalTuning:
    for name, value in (
        ("laser_accuracy_ghz", laser_accuracy_ghz),
        ("fabrication_offset_nm", fabrication_offset_nm),
        ("drift_nm_per_k", drift_nm_per_k),
        ("temperature_swing_k", temperature_swing_k),
    ):
        if not math.isfinite(value) or value < 0.0:
            raise ValueError(f"{name} must be finite and >= 0, got {value!r}")
    laser_nm = span_nm(laser_accuracy_ghz, wavelength_nm)
    drift_nm = drift_nm_per_k * temperature_swing_k
    required = laser_nm + fabrication_offset_nm + drift_nm
    range_nm = span_nm(spacing_ghz if barrel_shifting else fsr_ghz, wavelength_nm)
    return ThermalTuning(
        laser_accuracy_nm=laser_nm,
        fabrication_offset_nm=fabrication_offset_nm,
        drift_nm=drift_nm,
        required_nm=required,
        barrel_shifting=barrel_shifting,
        worst_case_range_nm=range_nm,
        exceeds_range=required > range_nm,
        heater_power_mw=heater_power_mw(range_nm, efficiency_nm_per_mw),
        efficiency_nm_per_mw=efficiency_nm_per_mw,
    )


class RingSummary(BaseModel):
    """A ring's derived parameters at one operating point (POST /ring)."""

    model_config = _FROZEN

    wavelength_nm: float
    f0_ghz: float
    q_loaded: float
    fwhm_ghz: float
    fwhm_nm: float
    fsr_ghz: float
    fsr_nm: float
    group_index: float | None
    length_um: float | None
    neighbor_rejection_db: dict[str, float]  # spacing (GHz) -> drop-port level, single Lorentzian


def ring_summary(
    wavelength_nm: float,
    q_loaded: float,
    fsr_ghz_value: float | None = None,
    group_index: float | None = None,
    diameter_um: float | None = None,
    spacings_ghz: tuple[float, ...] = (200.0, 400.0),
) -> RingSummary:
    """Ring parameters from either its FSR or its group index and diameter (and both checks)."""
    f0 = resonance_frequency_ghz(wavelength_nm)
    length = None if diameter_um is None else circumference_um(diameter_um)
    if fsr_ghz_value is None:
        if group_index is None or length is None:
            raise ValueError("give fsr_ghz, or group_index and diameter_um")
        fsr_value = fsr_ghz(group_index, length)
    else:
        fsr_value = _positive(fsr_ghz_value, "fsr_ghz")
        if group_index is None and length is not None:
            group_index = group_index_from_fsr(fsr_value, length)
    width = fwhm_ghz(f0, q_loaded)
    return RingSummary(
        wavelength_nm=wavelength_nm,
        f0_ghz=f0,
        q_loaded=q_loaded,
        fwhm_ghz=width,
        fwhm_nm=span_nm(width, wavelength_nm),
        fsr_ghz=fsr_value,
        fsr_nm=span_nm(fsr_value, wavelength_nm),
        group_index=group_index,
        length_um=length,
        neighbor_rejection_db={f"{s:g}": db(lorentzian(s, width)) for s in spacings_ghz},
    )
