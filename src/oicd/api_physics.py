"""Physics endpoints: microring, WDM grid and crosstalk, BiDi link, MPI, reference rack and pod.

Every number in a response is computed here by the engine (model card §12 to §14), including the
sampled ring spectra the explorer plots; the web only displays them.
"""

from typing import Literal

import numpy as np
from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field

from oicd.api_twin import catalog
from oicd.physics import ring, wdm
from oicd.physics.bidi import BidiLinkRequest, BidiLinkResult, evaluate_bidi_link
from oicd.physics.mpi import MpiResult, mpi_penalty_db
from oicd.serialize import canonical_json
from oicd.system.pod import PodResult, PodSpec, evaluate_pod
from oicd.system.rack import RackResult, evaluate_rack
from oicd.twin.physics import rack_spec

router = APIRouter()

_FROZEN = ConfigDict(frozen=True, extra="forbid")

MAX_SPECTRUM_POINTS = 4001


def _json(model: BaseModel) -> Response:
    return Response(content=canonical_json(model), media_type="application/json")


def _invalid(exc: Exception) -> JSONResponse:
    message = str(exc)
    return JSONResponse(
        status_code=422,
        content={
            "detail": message,
            "errors": [{"loc": [], "msg": message, "type": "invalid_input"}],
        },
    )


class Spectrum(BaseModel):
    """Drop-port response sampled for display: frequency (GHz), linear and dB."""

    model_config = _FROZEN

    frequency_ghz: tuple[float, ...]
    drop: tuple[float, ...]
    drop_db: tuple[float, ...]


def _spectrum(f_res: float, fwhm: float, fsr: float, f_lo: float, f_hi: float, n: int) -> Spectrum:
    freqs = np.linspace(f_lo, f_hi, n)
    drop = [ring.drop_response(float(f) - f_res, fwhm, fsr) for f in freqs.tolist()]
    return Spectrum(
        frequency_ghz=tuple(float(f) for f in freqs),
        drop=tuple(drop),
        drop_db=tuple(ring.db(v) for v in drop),
    )


class RingRequest(BaseModel):
    model_config = _FROZEN

    wavelength_nm: float = Field(default=1310.0, gt=0, allow_inf_nan=False)
    q_loaded: float = Field(gt=0, allow_inf_nan=False)
    fsr_ghz: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    group_index: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    diameter_um: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    spacings_ghz: tuple[float, ...] = (200.0, 400.0)
    symbol_rates_gbd: tuple[float, ...] = ()
    max_crosstalk_db: float = Field(default=-15.0, lt=0, allow_inf_nan=False)
    bandwidth_factor: float = Field(default=0.75, gt=0, allow_inf_nan=False)
    spectrum_span_ghz: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    spectrum_points: int = Field(default=401, ge=2, le=MAX_SPECTRUM_POINTS)


class RingResponse(BaseModel):
    model_config = _FROZEN

    summary: ring.RingSummary
    windows: tuple[ring.DesignWindow, ...]
    spectrum: Spectrum | None


@router.post("/ring", response_model=RingResponse)
def post_ring(request: RingRequest) -> Response:
    """Ring parameters (model card §13.1), design windows (§13.3) and a sampled drop response."""
    try:
        summary = ring.ring_summary(
            request.wavelength_nm,
            request.q_loaded,
            fsr_ghz_value=request.fsr_ghz,
            group_index=request.group_index,
            diameter_um=request.diameter_um,
            spacings_ghz=request.spacings_ghz,
        )
        windows = tuple(
            ring.design_window(
                summary.f0_ghz,
                spacing,
                baud,
                request.max_crosstalk_db,
                request.bandwidth_factor,
                q=request.q_loaded,
            )
            for baud in request.symbol_rates_gbd
            for spacing in request.spacings_ghz
        )
        span = request.spectrum_span_ghz
        spectrum = (
            None
            if span is None
            else _spectrum(
                summary.f0_ghz,
                summary.fwhm_ghz,
                summary.fsr_ghz,
                summary.f0_ghz - span / 2,
                summary.f0_ghz + span / 2,
                request.spectrum_points,
            )
        )
    except ValueError as exc:
        return _invalid(exc)
    return _json(RingResponse(summary=summary, windows=windows, spectrum=spectrum))


class GridRequest(BaseModel):
    model_config = _FROZEN

    center_nm: float = Field(default=1310.0, gt=0, allow_inf_nan=False)
    spacing_ghz: float = Field(default=200.0, gt=0, allow_inf_nan=False)
    count: int = Field(default=16, ge=1, le=128)


@router.post("/wdm/grid", response_model=wdm.Grid)
def post_wdm_grid(request: GridRequest) -> Response:
    """The interleaved grid of model card §13.5 (INFERENCE for the Guide grid)."""
    return _json(wdm.interleaved_grid(request.center_nm, request.spacing_ghz, request.count))


class CrosstalkRequest(BaseModel):
    model_config = _FROZEN

    center_nm: float = Field(default=1310.0, gt=0, allow_inf_nan=False)
    spacing_ghz: float = Field(default=200.0, gt=0, allow_inf_nan=False)
    count: int = Field(default=16, ge=2, le=128)
    q_loaded: float = Field(gt=0, allow_inf_nan=False)
    fsr_ghz: float = Field(gt=0, allow_inf_nan=False)
    receive: Literal["odd", "even"] = "odd"
    modulation: ring.Modulation = "NRZ"
    il_db: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    rl_db: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    spectrum_points: int = Field(default=0, ge=0, le=MAX_SPECTRUM_POINTS)
    margin_ghz: float = Field(default=300.0, ge=0, allow_inf_nan=False)


class RingSpectrum(BaseModel):
    model_config = _FROZEN

    channel: int
    drop_db: tuple[float, ...]


class CrosstalkResponse(BaseModel):
    model_config = _FROZEN

    grid: wdm.Grid
    fwhm_ghz: float
    receive_channels: tuple[int, ...]
    transmit_channels: tuple[int, ...]
    rings: tuple[wdm.RingLeakage, ...]
    worst: wdm.RingLeakage
    frequency_ghz: tuple[float, ...]
    spectra: tuple[RingSpectrum, ...]


def crosstalk(request: CrosstalkRequest) -> CrosstalkResponse:
    """Per-ring leakage and penalties for a BiDi grid (model card §13.2, §13.6), the worst
    receive channel, and sampled drop responses of every receive ring. ValueError if invalid."""
    grid = wdm.interleaved_grid(request.center_nm, request.spacing_ghz, request.count)
    first = 1 if request.receive == "odd" else 0
    receive = tuple(range(first, request.count, 2))
    transmit = tuple(range(1 - first, request.count, 2))
    fwhm = ring.fwhm_ghz(ring.resonance_frequency_ghz(request.center_nm), request.q_loaded)
    rings = tuple(
        wdm.ring_leakage(
            grid,
            n,
            fwhm,
            request.fsr_ghz,
            receive,
            transmit,
            request.modulation,
            request.il_db,
            request.rl_db,
        )
        for n in receive
    )
    worst = wdm.worst_channel(grid, rings)
    freqs: tuple[float, ...] = ()
    spectra: tuple[RingSpectrum, ...] = ()
    if request.spectrum_points:
        f_lo = grid.channels[0].frequency_ghz - request.margin_ghz
        f_hi = grid.channels[-1].frequency_ghz + request.margin_ghz
        freqs = tuple(float(f) for f in np.linspace(f_lo, f_hi, request.spectrum_points))
        spectra = tuple(
            RingSpectrum(
                channel=n,
                drop_db=tuple(
                    ring.db(
                        ring.drop_response(
                            f - grid.channels[n].frequency_ghz, fwhm, request.fsr_ghz
                        )
                    )
                    for f in freqs
                ),
            )
            for n in receive
        )
    return CrosstalkResponse(
        grid=grid,
        fwhm_ghz=fwhm,
        receive_channels=receive,
        transmit_channels=transmit,
        rings=rings,
        worst=worst,
        frequency_ghz=freqs,
        spectra=spectra,
    )


@router.post("/wdm/crosstalk", response_model=CrosstalkResponse)
def post_wdm_crosstalk(request: CrosstalkRequest) -> Response:
    """Per-ring leakage and penalties for a BiDi grid (model card §13.2, §13.6), the worst
    receive channel, and sampled drop responses of every receive ring for display."""
    try:
        result = crosstalk(request)
    except ValueError as exc:
        return _invalid(exc)
    return _json(result)


class SpectrumView(BaseModel):
    """The 16λ BiDi grid and its receive rings under one ring-FSR hypothesis, all inputs from
    the catalog (model card §13.5, §13.6, §14.5)."""

    model_config = _FROZEN

    hypothesis: str
    statement: str
    hypotheses: tuple[str, ...]
    q_loaded: float
    fsr_ghz: float
    accuracy_ghz: float  # the Guide grid's ± wavelength accuracy, drawn as bars per channel
    inputs: tuple[str, ...]  # catalog nodes the inputs come from
    crosstalk: CrosstalkResponse


SPECTRUM_HYPOTHESES = ("H_fsr18", "H_fsr32")


@router.get("/spectrum/bidi16", response_model=SpectrumView)
def get_spectrum(hypothesis: Literal["H_fsr18", "H_fsr32"] = "H_fsr18") -> Response:
    """Spectrum tab data: interleaved grid, ±accuracy, receive-ring responses (from the catalog)."""
    cat = catalog()
    h = cat.hypotheses[hypothesis]
    fsr_ghz = h.sets["bidi16.ring_fsr_thz"] * 1000.0
    inputs = (
        "bidi16.center_nm",
        "bidi16.txrx_spacing_ghz",
        "bidi16.lambda_count",
        "ring.mrm_q",
        "guide.wavelength_accuracy",
        "bidi16.channel_loss",
        "bidi16.return_loss_db",
    )
    v = {i: cat.nodes[i].nominal for i in inputs}  # type: ignore[union-attr]
    request = CrosstalkRequest(
        center_nm=v["bidi16.center_nm"],
        spacing_ghz=v["bidi16.txrx_spacing_ghz"],
        count=int(v["bidi16.lambda_count"]),
        q_loaded=v["ring.mrm_q"],
        fsr_ghz=fsr_ghz,
        receive="odd",
        il_db=v["bidi16.channel_loss"],
        rl_db=v["bidi16.return_loss_db"],
        spectrum_points=1601,
        margin_ghz=400.0,
    )
    return _json(
        SpectrumView(
            hypothesis=hypothesis,
            statement=h.statement,
            hypotheses=SPECTRUM_HYPOTHESES,
            q_loaded=request.q_loaded,
            fsr_ghz=fsr_ghz,
            accuracy_ghz=v["guide.wavelength_accuracy"],
            inputs=(*inputs, "bidi16.ring_fsr_thz"),
            crosstalk=crosstalk(request),
        )
    )


@router.post("/bidi/link", response_model=BidiLinkResult)
def post_bidi_link(request: BidiLinkRequest) -> Response:
    """Both directions of a BiDi link (model card §13.7)."""
    try:
        result = evaluate_bidi_link(request)
    except ValueError as exc:
        return _invalid(exc)
    return _json(result)


class MpiRequest(BaseModel):
    model_config = _FROZEN

    m_levels: int = Field(ge=2)
    er_db: float = Field(gt=0, allow_inf_nan=False)
    rt_db: float = Field(le=0, allow_inf_nan=False)
    rr_db: float = Field(le=0, allow_inf_nan=False)
    rc_db: float = Field(le=0, allow_inf_nan=False)
    n_connectors: int = Field(ge=0)
    n_max: int | None = Field(default=None, ge=0, le=64)


class MpiRow(BaseModel):
    model_config = _FROZEN

    n_connectors: int
    penalty_db: float | None  # None where the bound diverges (x >= 1)


class MpiResponse(BaseModel):
    model_config = _FROZEN

    result: MpiResult
    table: tuple[MpiRow, ...]


@router.post("/mpi", response_model=MpiResponse)
def post_mpi(request: MpiRequest) -> Response:
    """Worst-case MPI bound (model card §12.3), with an optional table over connector counts."""
    args = (request.m_levels, request.er_db, request.rt_db, request.rr_db, request.rc_db)
    try:
        result = mpi_penalty_db(*args, request.n_connectors)
    except ValueError as exc:
        return _invalid(exc)
    rows = []
    for n in range(0, (request.n_max if request.n_max is not None else -1) + 1):
        try:
            rows.append(MpiRow(n_connectors=n, penalty_db=mpi_penalty_db(*args, n).penalty_db))
        except ValueError:
            rows.append(MpiRow(n_connectors=n, penalty_db=None))
    return _json(MpiResponse(result=result, table=tuple(rows)))


class RackRequest(BaseModel):
    model_config = _FROZEN

    link_yields: tuple[float, ...] | None = None
    rack_yield_target: float | None = Field(default=None, gt=0, lt=1)


@router.post("/rack", response_model=RackResult)
def post_rack(request: RackRequest) -> Response:
    """The reference rack OICD-R64 (model card §14.9), built from the catalog (SYNTHETIC design)."""
    spec = rack_spec(catalog())
    update: dict[str, object] = {}
    if request.link_yields is not None:
        if not all(0.0 < y <= 1.0 for y in request.link_yields):
            return _invalid(ValueError("link yields must be in (0, 1]"))
        update["link_yields"] = request.link_yields
    if request.rack_yield_target is not None:
        update["rack_yield_target"] = request.rack_yield_target
    return _json(evaluate_rack(spec.model_copy(update=update)))


@router.post("/pod", response_model=PodResult)
def post_pod(request: PodSpec) -> Response:
    """Pod fibers, fiber length and connectors against the claims (model card §14.8)."""
    return _json(evaluate_pod(request))
