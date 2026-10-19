"""HTTP API over the engine. Physics lives in the engine modules; this module only validates
input, calls them and serializes.

Every response body is deterministic JSON (oicd.serialize). Invalid input, including invalid
physics and a unit-kind mismatch (model card T07, T12), returns 422 with
{"detail": <message>, "errors": [...]}, never a verdict.

Run: uv run uvicorn oicd.api:app --port 8000
"""

from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from oicd.api_physics import router as physics_router
from oicd.api_twin import router as twin_router
from oicd.display import Palette, palette
from oicd.profiles import PROFILES_DIR, load_link, profile_path
from oicd.provenance import DEFAULT_BIB_PATH, BibEntry, parse_bib_entries
from oicd.report import FeasibilityReport, evaluate
from oicd.schema import Link
from oicd.serialize import canonical_json
from oicd.statistics import (
    LABEL,
    MAX_BINS,
    MAX_SAMPLES,
    AnalyticYield,
    MonteCarloYield,
    analytic_yield,
    monte_carlo_yield,
)
from oicd.sweep import MAX_AXIS_POINTS, SweepResult, linspace, sweep
from oicd.tray import MAX_LANES, TrayReport, evaluate_tray
from oicd.units import UnitMismatchError

# The Vite dev server; no other origin may call the API from a browser.
ALLOWED_ORIGINS = ["http://localhost:5173"]

app = FastAPI(
    title="OICD feasibility engine",
    version="0.3.0",
    description="Independent model built from public information. Not affiliated with or "
    "endorsed by any company whose publications are cited.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

_REQUEST = ConfigDict(frozen=True, extra="forbid")


def _invalid(message: str, errors: list[dict[str, Any]]) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": message, "errors": errors})


def _from_errors(errors: list[Any]) -> JSONResponse:
    items = [
        {
            "loc": [str(part) for part in err.get("loc", ())],
            "msg": str(err.get("msg", "")),
            "type": str(err.get("type", "")),
        }
        for err in errors
    ]
    return _invalid("; ".join(f"{'.'.join(e['loc'])}: {e['msg']}" for e in items), items)


@app.exception_handler(RequestValidationError)
async def _request_invalid(_: Request, exc: RequestValidationError) -> JSONResponse:
    return _from_errors(list(exc.errors()))


@app.exception_handler(UnitMismatchError)
async def _unit_mismatch(_: Request, exc: UnitMismatchError) -> JSONResponse:
    # UnitMismatchError is a TypeError, which Pydantic does not turn into a validation error.
    return _invalid(str(exc), [{"loc": [], "msg": str(exc), "type": "unit_mismatch"}])


def _engine_invalid(exc: Exception) -> JSONResponse:
    if isinstance(exc, ValidationError):
        return _from_errors(list(exc.errors(include_url=False)))
    message = str(exc.args[0]) if isinstance(exc, KeyError) and exc.args else str(exc)
    return _invalid(message, [{"loc": [], "msg": message, "type": "invalid_input"}])


def _json(model: BaseModel) -> Response:
    return Response(content=canonical_json(model), media_type="application/json")


app.include_router(twin_router)
app.include_router(physics_router)


@app.get("/display", response_model=Palette)
def get_display(mode: Literal["light", "dark"] = "light", channels: int = 16) -> Response:
    """Every color the explorer uses: classes, status, margin scale, wavelength channels."""
    if not 1 <= channels <= 128:
        raise HTTPException(status_code=422, detail="channels must be 1 to 128")
    return _json(palette(mode, channels))


class ReferenceList(BaseModel):
    model_config = _REQUEST

    entries: tuple[BibEntry, ...]


@app.get("/references", response_model=ReferenceList)
def get_references() -> Response:
    """references.bib entries (title, year, url, note), so citations can link to their source."""
    entries = parse_bib_entries(DEFAULT_BIB_PATH.read_text(encoding="utf-8"))
    return _json(ReferenceList(entries=entries))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/evaluate", response_model=FeasibilityReport)
def evaluate_link(link: Link) -> Response:
    """Link JSON in, FeasibilityReport JSON out. TP2 is the transmitter's fixed launch_oma_min
    or is derived from its upstream chain (model card §10)."""
    return _json(evaluate(link))


class ProfileList(BaseModel):
    model_config = _REQUEST

    profiles: tuple[str, ...]


@app.get("/profiles", response_model=ProfileList)
def list_profiles() -> Response:
    names = sorted(p.stem for p in PROFILES_DIR.glob("*.json"))
    return _json(ProfileList(profiles=tuple(names)))


@app.get("/profiles/{name}", response_model=Link)
def get_profile(name: str) -> Response:
    try:
        path = profile_path(name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _json(load_link(path))


class AxisRequest(BaseModel):
    """One sweep axis: explicit values, or start, stop and num (np.linspace)."""

    model_config = _REQUEST

    path: str
    values: tuple[float, ...] | None = None
    start: float | None = None
    stop: float | None = None
    num: int | None = Field(default=None, ge=1, le=MAX_AXIS_POINTS)

    @model_validator(mode="after")
    def _one_form(self) -> "AxisRequest":
        ranged = (self.start, self.stop, self.num)
        if self.values is None and None in ranged:
            raise ValueError("give values, or start, stop and num")
        if self.values is not None and any(v is not None for v in ranged):
            raise ValueError("give values or start, stop and num, not both")
        return self

    def axis_values(self) -> tuple[float, ...]:
        if self.values is not None:
            return self.values
        assert self.start is not None and self.stop is not None and self.num is not None
        return linspace(self.start, self.stop, self.num)


class SweepRequest(BaseModel):
    model_config = _REQUEST

    link: Link
    x: AxisRequest
    y: AxisRequest


@app.post("/sweep", response_model=SweepResult)
def sweep_link(request: SweepRequest) -> Response:
    """Margin and verdict grids over two inputs (model card §8), at most 201 × 201."""
    try:
        result = sweep(
            request.link,
            request.x.path,
            request.x.axis_values(),
            request.y.path,
            request.y.axis_values(),
        )
    except (KeyError, ValueError) as exc:
        return _engine_invalid(exc)
    return _json(result)


class TrayRequest(BaseModel):
    model_config = _REQUEST

    name: str = "tray"
    lanes: tuple[Link, ...] = Field(min_length=1, max_length=MAX_LANES)


@app.post("/evaluate_tray", response_model=TrayReport)
def evaluate_tray_endpoint(request: TrayRequest) -> Response:
    """N lanes; EXCLUDED if any lane is, margin = minimum lane margin (model card §9)."""
    return _json(evaluate_tray(request.lanes, request.name))


class YieldRequest(BaseModel):
    model_config = _REQUEST

    link: Link
    n_samples: int = Field(default=100_000, ge=1, le=MAX_SAMPLES)
    seed: int = Field(default=0, ge=0)
    bins: int = Field(default=60, ge=1, le=MAX_BINS)


class YieldResponse(BaseModel):
    model_config = _REQUEST

    label: Literal["statistical, assumption-dependent"] = LABEL
    worst_case_verdict: Literal["NOT_EXCLUDED", "EXCLUDED"]
    worst_case_margin_db: float
    analytic: AnalyticYield
    monte_carlo: MonteCarloYield


@app.post("/yield", response_model=YieldResponse)
def yield_endpoint(request: YieldRequest) -> Response:
    """Statistical, assumption-dependent yield (model card §11). The worst-case verdict is
    reported unchanged next to it."""
    analytic = analytic_yield(request.link)
    mc = monte_carlo_yield(request.link, request.n_samples, request.seed, request.bins)
    return _json(
        YieldResponse(
            worst_case_verdict=analytic.worst_case_verdict,
            worst_case_margin_db=analytic.worst_case_margin_db,
            analytic=analytic,
            monte_carlo=mc,
        )
    )
