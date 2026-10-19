"""Design-space sweep (model card §8): margin and verdict over a 2D grid of two inputs.

Every cell is evaluated with the §3 (and §10) expressions in their summation order, using NumPy
broadcasting over the two axes, so a cell equals evaluate() of the edited link bit for bit.
Transcendental terms (10·log10 N, the OMA offset of an extinction ratio) are computed once per
axis value with the same scalar functions the engine uses. Pure and deterministic.
"""

import math
from collections.abc import Callable, Sequence
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict

from oicd.checks import Status
from oicd.checks.electrical import check_electrical
from oicd.paths import Unit, get_input, input_unit, set_input
from oicd.registry import EPSILON_DB, EPSILON_NM
from oicd.report import evaluate
from oicd.schema import Link
from oicd.units import DB, oma_offset_db
from oicd.upstream import split_loss_db

_FROZEN = ConfigDict(frozen=True, extra="forbid")

MAX_AXIS_POINTS = 201

Verdict = Literal["NOT_EXCLUDED", "EXCLUDED"]
Grid = np.ndarray | float


class SweepAxis(BaseModel):
    model_config = _FROZEN

    path: str
    unit: Unit
    values: tuple[float, ...]


class SweepCell(BaseModel):
    model_config = _FROZEN

    i: int
    j: int
    x: float
    y: float
    margin_db: float
    verdict: Verdict


class SweepResult(BaseModel):
    """margin_db[j][i] and verdict[j][i] at (x.values[i], y.values[j])."""

    model_config = _FROZEN

    x: SweepAxis
    y: SweepAxis
    margin_db: tuple[tuple[float, ...], ...]
    verdict: tuple[tuple[Verdict, ...], ...]
    design: SweepCell  # the unedited link; i and j are -1 when its values are not on the grid
    best: SweepCell
    worst: SweepCell
    contour_0db: tuple[tuple[tuple[float, float], tuple[float, float]], ...]  # segments


def _check_axis(path: str, values: Sequence[float]) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or not 1 <= array.size <= MAX_AXIS_POINTS:
        raise ValueError(f"{path}: an axis needs 1 to {MAX_AXIS_POINTS} values, got {array.size}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{path}: axis values must be finite")
    if array.size > 1 and not np.all(np.diff(array) > 0):
        raise ValueError(f"{path}: axis values must be strictly increasing")
    return array


def _margin_and_wavelength(
    link: Link, x_path: str, xs: np.ndarray, y_path: str, ys: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """M_net and the wavelength pass flag on the (ny, nx) grid, in the §3 and §10 order."""
    gx, gy = xs[np.newaxis, :], ys[:, np.newaxis]

    def term(path: str, base: float) -> Grid:
        if path == x_path:
            return gx
        if path == y_path:
            return gy
        return base

    def term_of(path: str, base: float, convert: Callable[[float], float]) -> Grid:
        """A term that is a scalar function of the input (split loss, OMA offset), evaluated once
        per axis value with the engine's own function."""
        if path == x_path:
            return np.array([convert(v) for v in xs.tolist()])[np.newaxis, :]
        if path == y_path:
            return np.array([convert(v) for v in ys.tolist()])[:, np.newaxis]
        return convert(base)

    tx = link.tx
    if tx.upstream is None:
        assert tx.launch_oma_min is not None
        launch: Grid = term("tx.launch_oma_min", tx.launch_oma_min.value.power_dbm.value)
    else:
        chain = tx.upstream
        power: Grid = term(
            "tx.upstream.laser_power_avg", chain.laser_power_avg.value.power_dbm.value
        )
        power = power - term("tx.upstream.laser_fiber_loss", chain.laser_fiber_loss.value.value)
        power = power - term("tx.upstream.coupling_loss", chain.coupling_loss.value.value)
        power = power - term_of(
            "tx.upstream.split_n",
            float(chain.split_n.value),
            lambda n: split_loss_db(int(n)).value,
        )
        power = power - term("tx.upstream.excess_loss", chain.excess_loss.value.value)
        power = power - term("tx.upstream.modulator_il", chain.modulator_il.value.value)
        power = power - term(
            "tx.upstream.output_coupler_loss", chain.output_coupler_loss.value.value
        )
        launch = power + term_of(
            "tx.upstream.extinction_ratio",
            chain.extinction_ratio.value.value,
            lambda er: oma_offset_db(DB(er)).value,
        )

    total: Grid = 0.0
    for i, element in enumerate(link.channel):
        total = total + term(f"channel[{i}].loss_max", element.loss_max.value.value)
    penalties: Grid = 0.0
    for i, penalty in enumerate(link.penalties):
        penalties = penalties + term(f"penalties[{i}].value", penalty.value.value.value)
    p_tp3 = launch - total
    sensitivity = term("rx.sensitivity_oma_max", link.rx.sensitivity_oma_max.value.power_dbm.value)
    margin = ((p_tp3 - sensitivity) - penalties) - term("reserve", link.reserve.value.value)

    center = term("tx.center_wavelength_nm", tx.center_wavelength_nm.value)
    tolerance = term("tx.wavelength_tolerance_nm", tx.wavelength_tolerance_nm.value)
    lower = (center - tolerance) - term("rx.passband_min_nm", link.rx.passband_min_nm.value)
    upper = term("rx.passband_max_nm", link.rx.passband_max_nm.value) - (center + tolerance)
    wavelength_ok = (np.asarray(lower) >= -EPSILON_NM) & (np.asarray(upper) >= -EPSILON_NM)

    shape = (ys.size, xs.size)
    return np.broadcast_to(np.asarray(margin, dtype=float), shape), np.broadcast_to(
        wavelength_ok, shape
    )


Point = tuple[float, float]


def _cross(va: float, vb: float, a: Point, b: Point) -> Point | None:
    """Where M = 0 on the edge a-b, by linear interpolation; None if M keeps its sign."""
    if (va >= 0.0) == (vb >= 0.0):
        return None
    t = va / (va - vb)
    return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))


def _contour_zero(xs: np.ndarray, ys: np.ndarray, m: np.ndarray) -> tuple[tuple[Point, Point], ...]:
    """Marching squares at M = 0 with linear interpolation along cell edges (§8)."""
    inside = m >= 0.0
    segments: list[tuple[Point, Point]] = []
    if m.shape[0] < 2 or m.shape[1] < 2:
        return ()
    corners = inside[:-1, :-1].astype(int) + inside[:-1, 1:] + inside[1:, 1:] + inside[1:, :-1]
    for j, i in zip(*np.nonzero((corners > 0) & (corners < 4)), strict=True):
        j, i = int(j), int(i)
        v00, v01 = float(m[j, i]), float(m[j, i + 1])
        v10, v11 = float(m[j + 1, i]), float(m[j + 1, i + 1])
        x0, x1, y0, y1 = float(xs[i]), float(xs[i + 1]), float(ys[j]), float(ys[j + 1])
        bottom = _cross(v00, v01, (x0, y0), (x1, y0))
        right = _cross(v01, v11, (x1, y0), (x1, y1))
        top = _cross(v10, v11, (x0, y1), (x1, y1))
        left = _cross(v00, v10, (x0, y0), (x0, y1))
        points = [p for p in (bottom, right, top, left) if p is not None]
        if len(points) == 2:
            segments.append((points[0], points[1]))
        elif len(points) == 4:
            assert bottom and right and top and left
            center_inside = (v00 + v01 + v10 + v11) / 4.0 >= 0.0
            # Saddle: bottom-left and top-right on one side, the other two on the other.
            if center_inside == (v00 >= 0.0):
                segments += [(bottom, right), (top, left)]
            else:
                segments += [(left, bottom), (right, top)]
    return tuple(segments)


def _cell(
    i: int, j: int, xs: np.ndarray, ys: np.ndarray, m: np.ndarray, ok: np.ndarray
) -> SweepCell:
    return SweepCell(
        i=i,
        j=j,
        x=float(xs[i]),
        y=float(ys[j]),
        margin_db=float(m[j, i]),
        verdict="NOT_EXCLUDED" if ok[j, i] else "EXCLUDED",
    )


def sweep(
    link: Link,
    x_path: str,
    x_values: Sequence[float],
    y_path: str,
    y_values: Sequence[float],
) -> SweepResult:
    """Margin and verdict grids over x_path × y_path (model card §8).

    Raises KeyError for an unknown or absent path and ValueError for an oversized, unordered or
    non-finite axis, for x_path == y_path, or for a value that is invalid physics for its input.
    """
    if x_path == y_path:
        raise ValueError("x and y must be different inputs")
    x_unit, y_unit = input_unit(link, x_path), input_unit(link, y_path)
    xs, ys = _check_axis(x_path, x_values), _check_axis(y_path, y_values)
    # Each value must be valid physics for its input (T12 rules), checked by the schema itself.
    for path, axis in ((x_path, xs), (y_path, ys)):
        for value in axis.tolist():
            set_input(link, path, value)
    if {x_path, y_path} == {"rx.passband_min_nm", "rx.passband_max_nm"}:
        low, high = (xs, ys) if x_path == "rx.passband_min_nm" else (ys, xs)
        if not float(low.max()) < float(high.min()):
            raise ValueError("passband_min_nm must be < passband_max_nm at every grid point")

    margin, wavelength_ok = _margin_and_wavelength(link, x_path, xs, y_path, ys)
    electrical_ok = check_electrical(link).status is Status.PASS
    ok = electrical_ok & wavelength_ok & (margin >= -EPSILON_DB)

    flat_best, flat_worst = int(np.argmax(margin)), int(np.argmin(margin))
    best = _cell(flat_best % xs.size, flat_best // xs.size, xs, ys, margin, ok)
    worst = _cell(flat_worst % xs.size, flat_worst // xs.size, xs, ys, margin, ok)

    report = evaluate(link)
    x0, y0 = get_input(link, x_path), get_input(link, y_path)
    on_x, on_y = np.flatnonzero(xs == x0), np.flatnonzero(ys == y0)
    design = SweepCell(
        i=int(on_x[0]) if on_x.size else -1,
        j=int(on_y[0]) if on_y.size else -1,
        x=x0,
        y=y0,
        margin_db=report.margin_db,
        verdict=report.verdict,
    )

    def as_rows(grid: np.ndarray) -> tuple[tuple[float, ...], ...]:
        return tuple(tuple(float(v) for v in row) for row in grid.tolist())

    return SweepResult(
        x=SweepAxis(path=x_path, unit=x_unit, values=tuple(xs.tolist())),
        y=SweepAxis(path=y_path, unit=y_unit, values=tuple(ys.tolist())),
        margin_db=as_rows(margin),
        verdict=tuple(
            tuple("NOT_EXCLUDED" if v else "EXCLUDED" for v in row) for row in ok.tolist()
        ),
        design=design,
        best=best,
        worst=worst,
        contour_0db=_contour_zero(xs, ys, margin),
    )


def linspace(start: float, stop: float, num: int) -> tuple[float, ...]:
    """Evenly spaced axis values, as np.linspace (start and stop included)."""
    if not 1 <= num <= MAX_AXIS_POINTS:
        raise ValueError(f"num must be 1 to {MAX_AXIS_POINTS}, got {num}")
    if not (math.isfinite(start) and math.isfinite(stop)):
        raise ValueError("start and stop must be finite")
    return tuple(float(v) for v in np.linspace(start, stop, num))
