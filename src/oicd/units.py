"""Logarithmic power units, optical power kinds and unit conversions.

Allowed arithmetic (everything else raises TypeError):
    DBm - DB  -> DBm
    DBm + DB  -> DBm
    DBm - DBm -> DB
    DB + DB   -> DB
    DB - DB   -> DB
    -DB       -> DB
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from numbers import Real

# Speed of light in vacuum. Exact by definition of the SI metre (2019 SI).
C_M_PER_S = 299_792_458


class UnitMismatchError(TypeError):
    """Raised when quantities of incompatible kinds (e.g. OMA vs average) are mixed."""


def _finite_float(value: object, unit: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{unit} value must be a real number, got {value!r}")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{unit} value must be finite, got {result!r}")
    return result


@dataclass(frozen=True, slots=True, order=True)
class DB:
    """A power ratio in decibels."""

    value: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _finite_float(self.value, "dB"))

    def __add__(self, other: object) -> DB:
        if type(other) is DB:
            return DB(self.value + other.value)
        return NotImplemented

    def __sub__(self, other: object) -> DB:
        if type(other) is DB:
            return DB(self.value - other.value)
        return NotImplemented

    def __neg__(self) -> DB:
        return DB(-self.value)


@dataclass(frozen=True, slots=True, order=True)
class DBm:
    """An absolute power level in decibels relative to 1 mW."""

    value: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _finite_float(self.value, "dBm"))

    def __add__(self, other: object) -> DBm:
        if type(other) is DB:
            return DBm(self.value + other.value)
        return NotImplemented

    def __sub__(self, other: object) -> DBm | DB:
        if type(other) is DB:
            return DBm(self.value - other.value)
        if type(other) is DBm:
            return DB(self.value - other.value)
        return NotImplemented


class PowerKind(StrEnum):
    OMA = "oma"
    AVERAGE = "average"


@dataclass(frozen=True, slots=True)
class OpticalPower:
    """An optical power level tagged with how it is measured (OMA or average)."""

    power_dbm: DBm
    kind: PowerKind

    def __post_init__(self) -> None:
        if type(self.power_dbm) is not DBm:
            raise TypeError(f"power_dbm must be DBm, got {self.power_dbm!r}")
        if not isinstance(self.kind, PowerKind):
            raise TypeError(f"kind must be PowerKind, got {self.kind!r}")

    def _require_same_kind(self, other: OpticalPower) -> None:
        if self.kind is not other.kind:
            raise UnitMismatchError(
                f"cannot combine {self.kind.value} and {other.kind.value} optical power"
            )

    def __add__(self, other: object) -> OpticalPower:
        if type(other) is DB:
            return OpticalPower(self.power_dbm + other, self.kind)
        if type(other) is OpticalPower:
            # Kind mismatch is reported first; same-kind power + power is still
            # forbidden, like DBm + DBm.
            self._require_same_kind(other)
        return NotImplemented

    def __sub__(self, other: object) -> OpticalPower | DB:
        if type(other) is DB:
            return OpticalPower(self.power_dbm - other, self.kind)
        if type(other) is OpticalPower:
            self._require_same_kind(other)
            return self.power_dbm - other.power_dbm
        return NotImplemented


def mw_to_dbm(p_mw: float) -> DBm:
    p = _finite_float(p_mw, "mW")
    if p <= 0.0:
        raise ValueError(f"power must be positive to express in dBm, got {p} mW")
    return DBm(10.0 * math.log10(p))


def dbm_to_mw(p: DBm) -> float:
    if type(p) is not DBm:
        raise TypeError(f"expected DBm, got {p!r}")
    return 10.0 ** (p.value / 10.0)


def avg_to_oma(p_avg: OpticalPower, er_db: DB) -> OpticalPower:
    """Convert average power to OMA: OMA = 2 * P_avg * (ER - 1) / (ER + 1), ER linear."""
    if type(p_avg) is not OpticalPower:
        raise TypeError(f"expected OpticalPower, got {p_avg!r}")
    if type(er_db) is not DB:
        raise TypeError(f"extinction ratio must be DB, got {er_db!r}")
    if p_avg.kind is not PowerKind.AVERAGE:
        raise UnitMismatchError(f"avg_to_oma needs average power, got {p_avg.kind.value}")
    if er_db.value <= 0.0:
        raise ValueError(f"extinction ratio must be > 0 dB, got {er_db.value} dB")
    p_avg_mw = dbm_to_mw(p_avg.power_dbm)
    er = 10.0 ** (er_db.value / 10.0)
    oma_mw = 2.0 * p_avg_mw * (er - 1.0) / (er + 1.0)
    return OpticalPower(mw_to_dbm(oma_mw), PowerKind.OMA)


def oma_offset_db(er_db: DB) -> DB:
    """OMA relative to average power for extinction ratio ER (linear): 10·log10(2(ER−1)/(ER+1)).

    The §3 conversion OMA = 2·P_avg·(ER − 1)/(ER + 1) in dB form, so OMA_dBm = P_avg,dBm + offset.
    """
    if type(er_db) is not DB:
        raise TypeError(f"extinction ratio must be DB, got {er_db!r}")
    if er_db.value <= 0.0:
        raise ValueError(f"extinction ratio must be > 0 dB, got {er_db.value} dB")
    er = 10.0 ** (er_db.value / 10.0)
    return DB(10.0 * math.log10(2.0 * (er - 1.0) / (er + 1.0)))


def delta_lambda_nm(lambda_nm: float, delta_f_ghz: float) -> float:
    """Wavelength span for a frequency span: delta_lambda ~= lambda^2 * delta_f / c."""
    lam_nm = _finite_float(lambda_nm, "nm")
    df_ghz = _finite_float(delta_f_ghz, "GHz")
    if lam_nm <= 0.0:
        raise ValueError(f"wavelength must be positive, got {lam_nm} nm")
    lam_m = lam_nm * 1e-9
    df_hz = df_ghz * 1e9
    return lam_m**2 * df_hz / C_M_PER_S * 1e9
