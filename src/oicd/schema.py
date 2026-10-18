"""Link description: transmitter, receiver, passive channel, penalties and reserve.

Every physical number is a Quantity carrying Provenance. Invalid physics raises ValueError
(Pydantic's ValidationError) at construction; a TX or RX power that is not OMA raises
UnitMismatchError.
"""

import math
from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from oicd.provenance import Provenance, Quantity
from oicd.units import DB, OpticalPower, PowerKind, UnitMismatchError

_FROZEN = ConfigDict(frozen=True, extra="forbid")


class FEC(StrEnum):
    RS_544_514 = "RS(544,514)"
    NONE = "none"


_FEC_ALIASES = {"KP4": FEC.RS_544_514}


def _check_bound(
    value: float, field: str, *, gt: float | None = None, ge: float | None = None
) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{field} must be finite, got {value!r}")
    if gt is not None and not value > gt:
        raise ValueError(f"{field} must be > {gt}, got {value!r}")
    if ge is not None and not value >= ge:
        raise ValueError(f"{field} must be >= {ge}, got {value!r}")


def _require_oma(q: Quantity[OpticalPower], field: str) -> None:
    if q.value.kind is not PowerKind.OMA:
        raise UnitMismatchError(f"{field} must be OMA, got {q.value.kind.value}")


class ElectricalInterface(BaseModel):
    model_config = _FROZEN

    modulation: Literal["NRZ", "PAM4"]
    symbol_rate_gbd: float = Field(gt=0, allow_inf_nan=False)
    lanes: int = Field(ge=1)
    fec: FEC
    provenance: Provenance

    @field_validator("fec", mode="before")
    @classmethod
    def _resolve_fec_alias(cls, value: object) -> object:
        if isinstance(value, str) and not isinstance(value, FEC):
            return _FEC_ALIASES.get(value, value)
        return value


class Transmitter(BaseModel):
    model_config = _FROZEN

    name: str
    electrical: ElectricalInterface
    center_wavelength_nm: Quantity[float]
    wavelength_tolerance_nm: Quantity[float]
    launch_oma_min: Quantity[OpticalPower]  # at TP2

    @field_validator("center_wavelength_nm")
    @classmethod
    def _positive_wavelength(cls, q: Quantity[float]) -> Quantity[float]:
        _check_bound(q.value, "center_wavelength_nm", gt=0.0)
        return q

    @field_validator("wavelength_tolerance_nm")
    @classmethod
    def _non_negative_tolerance(cls, q: Quantity[float]) -> Quantity[float]:
        _check_bound(q.value, "wavelength_tolerance_nm", ge=0.0)
        return q

    @field_validator("launch_oma_min")
    @classmethod
    def _launch_is_oma(cls, q: Quantity[OpticalPower]) -> Quantity[OpticalPower]:
        _require_oma(q, "launch_oma_min")
        return q


class Receiver(BaseModel):
    model_config = _FROZEN

    name: str
    electrical: ElectricalInterface
    passband_min_nm: Quantity[float]
    passband_max_nm: Quantity[float]
    sensitivity_oma_max: Quantity[OpticalPower]  # at TP3

    @field_validator("passband_min_nm")
    @classmethod
    def _positive_min(cls, q: Quantity[float]) -> Quantity[float]:
        _check_bound(q.value, "passband_min_nm", gt=0.0)
        return q

    @field_validator("passband_max_nm")
    @classmethod
    def _finite_max(cls, q: Quantity[float]) -> Quantity[float]:
        _check_bound(q.value, "passband_max_nm", gt=0.0)
        return q

    @field_validator("sensitivity_oma_max")
    @classmethod
    def _sensitivity_is_oma(cls, q: Quantity[OpticalPower]) -> Quantity[OpticalPower]:
        _require_oma(q, "sensitivity_oma_max")
        return q

    @model_validator(mode="after")
    def _ordered_passband(self) -> Self:
        if not self.passband_min_nm.value < self.passband_max_nm.value:
            raise ValueError(
                f"passband_min_nm ({self.passband_min_nm.value}) must be < "
                f"passband_max_nm ({self.passband_max_nm.value})"
            )
        return self


class LossElement(BaseModel):
    model_config = _FROZEN

    name: str
    loss_max: Quantity[DB]

    @field_validator("loss_max")
    @classmethod
    def _non_negative_loss(cls, q: Quantity[DB]) -> Quantity[DB]:
        _check_bound(q.value.value, "loss_max", ge=0.0)
        return q


class Penalty(BaseModel):
    model_config = _FROZEN

    name: str
    value: Quantity[DB]

    @field_validator("value")
    @classmethod
    def _non_negative_penalty(cls, q: Quantity[DB]) -> Quantity[DB]:
        _check_bound(q.value.value, "penalty", ge=0.0)
        return q


class Link(BaseModel):
    model_config = _FROZEN

    name: str = "unnamed link"
    tx: Transmitter
    rx: Receiver
    channel: tuple[LossElement, ...]
    penalties: tuple[Penalty, ...] = ()
    reserve: Quantity[DB]

    @field_validator("reserve")
    @classmethod
    def _non_negative_reserve(cls, q: Quantity[DB]) -> Quantity[DB]:
        _check_bound(q.value.value, "reserve", ge=0.0)
        return q
