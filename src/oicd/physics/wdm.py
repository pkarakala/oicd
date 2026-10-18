"""WDM grid, ring leakage and aliasing (model card §13.5, §13.6).

Guide grid (INFERENCE): f_n = c/λ_c + (n − (N − 1)/2)·spacing, n = 0 … N − 1; even n on grid A, odd
n on grid B (two grids at twice the spacing, interleaved). Lightmatter says "centered at 1310 nm"
but gives no channel frequencies, so the grid is OICD's inference.

For a ring on channel n with FSR F: leakage X = Σ T_n(f_m) over the co-directional channels m ≠ n,
reflected leakage X_r = Σ T_n(f_m) over the counter-directional (local transmit) channels, whose
inbound reflections travel with the signal and are dropped like signal. Outbound counter-directional
light couples to the ring's other circulation and is not dropped; backscatter into the forward mode
is the residual path and is NOT_EVALUATED.
"""

import math
from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel, ConfigDict

from oicd.physics.ring import (
    IMAGES,
    Modulation,
    crosstalk_penalty,
    drop_response,
    resonance_frequency_ghz,
    wavelength_nm,
)

_FROZEN = ConfigDict(frozen=True, extra="forbid")

# A float tolerance for "an image lands exactly on a channel" (GHz), not a physical parameter.
ALIAS_TOL_GHZ = 1e-6
# Worst-channel ranking: totals within this many dB are ties (truncation of the image sum at
# k = ±50 moves physically identical channels by ~1e-8 dB).
TIE_DB = 1e-6

Direction = Literal["co", "counter"]


class Channel(BaseModel):
    model_config = _FROZEN

    index: int
    frequency_ghz: float
    wavelength_nm: float
    grid: Literal["A", "B"]


class Grid(BaseModel):
    model_config = _FROZEN

    center_nm: float
    spacing_ghz: float
    channels: tuple[Channel, ...]
    span_nm: float  # λ_0 − λ_(N−1), outer channels
    source_class: Literal["inference"] = "inference"


def interleaved_grid(
    center_nm: float = 1310.0, spacing_ghz: float = 200.0, count: int = 16
) -> Grid:
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError(f"count must be an integer >= 1, got {count!r}")
    if not math.isfinite(spacing_ghz) or spacing_ghz <= 0.0:
        raise ValueError(f"spacing_ghz must be > 0, got {spacing_ghz!r}")
    f_c = resonance_frequency_ghz(center_nm)
    channels = []
    for n in range(count):
        f = f_c + (n - (count - 1) / 2.0) * spacing_ghz
        channels.append(
            Channel(
                index=n,
                frequency_ghz=f,
                wavelength_nm=wavelength_nm(f),
                grid="A" if n % 2 == 0 else "B",
            )
        )
    return Grid(
        center_nm=center_nm,
        spacing_ghz=spacing_ghz,
        channels=tuple(channels),
        span_nm=channels[0].wavelength_nm - channels[-1].wavelength_nm,
    )


class Image(BaseModel):
    """A resonance order k ≠ 0 of a ring that lands exactly on a grid channel."""

    model_config = _FROZEN

    order: int
    channel: int
    direction: Direction
    effect: str


def aliasing(
    grid: Grid, ring_channel: int, fsr_ghz: float, counter: Sequence[int]
) -> tuple[Image, ...]:
    """Images of the ring on channel ring_channel that land on grid channels (§13.6)."""
    f_ring = grid.channels[ring_channel].frequency_ghz
    out = []
    for ch in grid.channels:
        if ch.index == ring_channel:
            continue
        ratio = (ch.frequency_ghz - f_ring) / fsr_ghz
        k = round(ratio)
        if k != 0 and abs(ch.frequency_ghz - f_ring - k * fsr_ghz) < ALIAS_TOL_GHZ:
            is_counter = ch.index in counter
            out.append(
                Image(
                    order=k,
                    channel=ch.index,
                    direction="counter" if is_counter else "co",
                    effect=(
                        "inbound reflections of this local transmitter are dropped like signal; "
                        "outbound light is not dropped (backscatter NOT_EVALUATED)"
                        if is_counter
                        else "co-directional channel dropped as crosstalk"
                    ),
                )
            )
    return tuple(out)


class RingLeakage(BaseModel):
    model_config = _FROZEN

    channel: int
    leakage: float  # X over co-directional channels
    reflected_leakage: float  # X_r over counter-directional (local transmit) channels
    crosstalk_db: float  # −10·log10(1 − k·X)
    crosstalk_alternative_db: float  # 10·log10(1 + X)
    reflection_db: float | None  # bhatt2001 with R·X_r, when il_db and rl_db are given
    total_db: float
    images: tuple[Image, ...]


def ring_leakage(
    grid: Grid,
    ring_channel: int,
    fwhm_ghz: float,
    fsr_ghz: float,
    co: Sequence[int],
    counter: Sequence[int],
    modulation: Modulation,
    il_db: float | None = None,
    rl_db: float | None = None,
    images: int = IMAGES,
) -> RingLeakage:
    """X and X_r for one receive ring, and the penalties they cause (§13.2, §13.6, §12.4)."""
    f_ring = grid.channels[ring_channel].frequency_ghz

    def t(m: int) -> float:
        return drop_response(grid.channels[m].frequency_ghz - f_ring, fwhm_ghz, fsr_ghz, images)

    x = sum(t(m) for m in co if m != ring_channel)
    xr = sum(t(m) for m in counter)
    penalty = crosstalk_penalty(x, modulation)
    reflection = None
    if il_db is not None and rl_db is not None:
        trans = 10.0 ** (-il_db / 10.0)
        r_eff = 10.0 ** (-rl_db / 10.0) * xr
        if r_eff >= trans:
            raise ValueError("reflected local-transmitter light is not below the signal")
        reflection = 10.0 * math.log10(trans / (trans - r_eff))
    return RingLeakage(
        channel=ring_channel,
        leakage=x,
        reflected_leakage=xr,
        crosstalk_db=penalty.penalty_db,
        crosstalk_alternative_db=penalty.alternative_db,
        reflection_db=reflection,
        total_db=penalty.penalty_db + (reflection or 0.0),
        images=aliasing(grid, ring_channel, fsr_ghz, counter),
    )


def worst_channel(grid: Grid, rings: Sequence[RingLeakage]) -> RingLeakage:
    """Largest total penalty; totals within TIE_DB are ties, broken by distance to the grid centre
    (the channel with neighbors on both sides), then by the lower index (model card §13.6)."""
    if not rings:
        raise ValueError("no rings")
    top = max(r.total_db for r in rings)
    tied = [r for r in rings if top - r.total_db <= TIE_DB]
    centre = (len(grid.channels) - 1) / 2.0
    return min(tied, key=lambda r: (abs(r.channel - centre), r.channel))
