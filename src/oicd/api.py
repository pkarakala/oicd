"""HTTP API over the engine. Physics lives in oicd.checks and oicd.report; this module only
validates input, calls evaluate() and serializes.

Run: uv run uvicorn oicd.api:app --port 8000
"""

from typing import Annotated, Any

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError

from oicd.profiles import load_link, profile_path
from oicd.report import evaluate
from oicd.schema import Link
from oicd.units import UnitMismatchError

# The Vite dev server; no other origin may call the API from a browser.
ALLOWED_ORIGINS = ["http://localhost:5173"]

app = FastAPI(title="OICD feasibility engine", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def _invalid(message: str, errors: list[dict[str, Any]]) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": message, "errors": errors})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/evaluate")
def evaluate_link(payload: Annotated[dict[str, Any], Body()]) -> Response:
    """Link JSON in, FeasibilityReport JSON out. Invalid physics or a unit-kind mismatch is
    invalid input (model card T07, T12) and returns 422, never a verdict."""
    try:
        link = Link.model_validate(payload)
    except ValidationError as exc:
        errors = [
            {"loc": [str(part) for part in err["loc"]], "msg": err["msg"], "type": err["type"]}
            for err in exc.errors(include_url=False)
        ]
        return _invalid("; ".join(f"{'.'.join(e['loc'])}: {e['msg']}" for e in errors), errors)
    except UnitMismatchError as exc:
        return _invalid(str(exc), [{"loc": [], "msg": str(exc), "type": "unit_mismatch"}])
    return Response(content=evaluate(link).to_json(), media_type="application/json")


@app.get("/profiles/{name}")
def get_profile(name: str) -> dict[str, Any]:
    try:
        path = profile_path(name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return load_link(path).model_dump(mode="json")
