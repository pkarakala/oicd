"""Link description: transmitter, receiver, passive channel, penalties and reserve.

Every physical number is a Quantity carrying Provenance. Invalid physics raises ValueError
(Pydantic's ValidationError) at construction; a TX or RX power that is not OMA raises
UnitMismatchError. The transmitter gives TP2 either as a fixed OMA or as an upstream chain from
the laser (model card §10), never both.
"""

import math
from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

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


def _non_negative_db(q: Quantity[DB], field: str) -> Quantity[DB]:
    _check_bound(q.value.value, field, ge=0.0)
    return q


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


class UpstreamChain(BaseModel):
    """Laser to TP2 (model card §10). Losses in dB, applied in field order to average power."""

    model_config = _FROZEN

    name: str = "upstream chain"
    laser_power_avg: Quantity[OpticalPower]  # per laser output fiber, AVERAGE
    laser_fiber_loss: Quantity[DB]  # laser fiber and connector to the PIC
    coupling_loss: Quantity[DB]  # fiber to PIC
    split_n: Quantity[int]  # ideal 1:N split, 10·log10(N)
    excess_loss: Quantity[DB]  # split excess
    modulator_il: Quantity[DB]
    output_coupler_loss: Quantity[DB]  # to TP2
    extinction_ratio: Quantity[DB]

    @field_validator("laser_power_avg")
    @classmethod
    def _laser_is_average(cls, q: Quantity[OpticalPower]) -> Quantity[OpticalPower]:
        if q.value.kind is not PowerKind.AVERAGE:
            raise UnitMismatchError(f"laser_power_avg must be AVERAGE, got {q.value.kind.value}")
        return q

    @field_validator(
        "laser_fiber_loss", "coupling_loss", "excess_loss", "modulator_il", "output_coupler_loss"
    )
    @classmethod
    def _losses_non_negative(cls, q: Quantity[DB], info: ValidationInfo) -> Quantity[DB]:
        return _non_negative_db(q, str(info.field_name))

    @field_validator("split_n")
    @classmethod
    def _split_at_least_one(cls, q: Quantity[int]) -> Quantity[int]:
        if isinstance(q.value, bool) or q.value < 1:
            raise ValueError(f"split_n must be an integer >= 1, got {q.value!r}")
        return q

    @field_validator("extinction_ratio")
    @classmethod
    def _er_positive(cls, q: Quantity[DB]) -> Quantity[DB]:
        _check_bound(q.value.value, "extinction_ratio", gt=0.0)
        return q


class Transmitter(BaseModel):
    model_config = _FROZEN

    name: str
    electrical: ElectricalInterface
    center_wavelength_nm: Quantity[float]
    wavelength_tolerance_nm: Quantity[float]
    launch_oma_min: Quantity[OpticalPower] | None = None  # at TP2, fixed
    upstream: UpstreamChain | None = None  # or TP2 derived from the laser (§10)

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
    def _launch_is_oma(cls, q: Quantity[OpticalPower] | None) -> Quantity[OpticalPower] | None:
        if q is not None:
            _require_oma(q, "launch_oma_min")
        return q

    @model_validator(mode="after")
    def _one_tp2_source(self) -> Self:
        if (self.launch_oma_min is None) == (self.upstream is None):
            raise ValueError("give exactly one of launch_oma_min (fixed TP2) and upstream (chain)")
        return self


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


class LossDistribution(BaseModel):
    """Normal distribution of a loss for the statistical budget (model card §11). SYNTHETIC."""

    model_config = _FROZEN

    mean: Quantity[DB]
    sigma: Quantity[DB]

    @field_validator("mean", "sigma")
    @classmethod
    def _non_negative(cls, q: Quantity[DB], info: ValidationInfo) -> Quantity[DB]:
        return _non_negative_db(q, str(info.field_name))


class LossElement(BaseModel):
    model_config = _FROZEN

    name: str
    loss_max: Quantity[DB]  # worst case, decides the verdict (§3)
    loss_distribution: LossDistribution | None = None  # statistical budget only (§11)

    @field_validator("loss_max")
    @classmethod
    def _non_negative_loss(cls, q: Quantity[DB]) -> Quantity[DB]:
        return _non_negative_db(q, "loss_max")


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
