"""Twin endpoints: the catalog, its evaluated inference graphs and physics, and part geometry.

GET  /catalog                  products with counts and hypotheses
GET  /catalog/{product}        evaluated graph (facts, assumptions, derived values with intervals
                               and derivations, checks, conflicts, support matrix, tornado), physics
POST /inference/{product}      the same with assumption overrides and a hypothesis choice
GET  /geometry                 scene names
GET  /geometry/{scene}         a scene's parts, each with its dims_class, the evaluated catalog
                               nodes its parts name, its tour captions, and source issues
GET  /overlay/{scene}          light paths, pulses, margins and heater power on the scene's parts
"""

import functools
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict

from oicd.serialize import canonical_json
from oicd.twin.catalog import (
    GEOMETRY_DIR,
    Catalog,
    CatalogError,
    GeometryScene,
    SceneInfo,
    TourStop,
    load_catalog,
    load_geometry,
    validate_geometry_sources,
)
from oicd.twin.formulas import with_unit
from oicd.twin.inference import CheckOutcome, EvaluatedGraph, NodeResult, evaluate_graph
from oicd.twin.overlay import L20_CASE_ISOLATION_DB, Overlay, OverlayError, overlay_for
from oicd.twin.physics import EVALUATIONS, ProductPhysics, physics_for

router = APIRouter()

_FROZEN = ConfigDict(frozen=True, extra="forbid")

INDEPENDENCE = (
    "Independent reconstruction from public information. Not affiliated with or endorsed by "
    "Lightmatter. Product names belong to their owners."
)


@functools.lru_cache(maxsize=1)
def catalog() -> Catalog:
    """The shipped catalog, loaded once (read-only)."""
    return load_catalog()


@functools.lru_cache(maxsize=1)
def catalog_graph() -> EvaluatedGraph:
    """The whole catalog evaluated once, with no overrides or hypotheses (read-only)."""
    return evaluate_graph(catalog(), None)


class HypothesisInfo(BaseModel):
    model_config = _FROZEN

    id: str
    statement: str
    group: str
    sets: dict[str, float]


class ProductSummary(BaseModel):
    model_config = _FROZEN

    id: str
    name: str
    family: str
    kind: Literal["product", "reference", "system"]
    status: str
    summary: str
    facts: int
    verified_facts: int
    assumptions: int
    derived: int
    checks: int
    hypotheses: tuple[HypothesisInfo, ...]
    has_physics: bool
    has_geometry: bool


class CatalogIndex(BaseModel):
    model_config = _FROZEN

    independence: str
    products: tuple[ProductSummary, ...]


class ProductView(BaseModel):
    model_config = _FROZEN

    independence: str
    product: ProductSummary
    graph: EvaluatedGraph
    physics: ProductPhysics | None


class InferenceRequest(BaseModel):
    model_config = _FROZEN

    overrides: dict[str, float] = {}
    hypotheses: tuple[str, ...] = ()


class SceneList(BaseModel):
    model_config = _FROZEN

    scenes: tuple[str, ...]
    info: tuple[SceneInfo, ...]  # in the same order: names, units, parents and products


class Caption(BaseModel):
    """A tour stop's caption, written by the engine from the catalog."""

    model_config = _FROZEN

    part: str
    ref: str  # the catalog node or check the caption comes from; "" for a written note
    text: str
    badge: str  # the node's source class, the check's status, or "note"


class SceneView(BaseModel):
    model_config = _FROZEN

    independence: str
    scene: GeometryScene
    source_issues: tuple[str, ...]
    nodes: tuple[NodeResult, ...]  # every catalog node the parts and the tour name, evaluated
    checks: tuple[CheckOutcome, ...]  # every check the tour names
    captions: tuple[Caption, ...]  # one per tour stop, in order


def _json(model: BaseModel) -> Response:
    return Response(content=canonical_json(model), media_type="application/json")


def _summary(cat: Catalog, stem: str) -> ProductSummary:
    f = cat.files[stem]
    return ProductSummary(
        id=stem,
        name=f.product.name,
        family=f.product.family,
        kind=f.product.kind,
        status=f.product.status,
        summary=f.product.summary,
        facts=len(f.fact),
        verified_facts=sum(x.verified for x in f.fact),
        assumptions=len(f.assumption),
        derived=len(f.derived),
        checks=len(f.check),
        hypotheses=tuple(
            HypothesisInfo(id=h.id, statement=h.statement, group=h.group, sets=h.sets)
            for h in f.hypothesis
        ),
        has_physics=stem in EVALUATIONS,
        has_geometry=(GEOMETRY_DIR / f"{stem}.toml").is_file(),
    )


def _view(product: str, request: InferenceRequest) -> Response:
    cat = catalog()
    if product not in cat.files:
        raise HTTPException(status_code=404, detail=f"no catalog product {product!r}")
    try:
        graph = evaluate_graph(cat, product, request.overrides, request.hypotheses)
    except (KeyError, CatalogError) as exc:
        message = str(exc.args[0]) if isinstance(exc, KeyError) and exc.args else str(exc)
        raise HTTPException(status_code=422, detail=message) from exc
    return _json(
        ProductView(
            independence=INDEPENDENCE,
            product=_summary(cat, product),
            graph=graph,
            physics=physics_for(cat, product),
        )
    )


def _caption(
    stop: TourStop, nodes: dict[str, NodeResult], checks: dict[str, CheckOutcome]
) -> Caption:
    if stop.node in nodes:
        n = nodes[stop.node]
        text = n.derivation if n.nominal is None else f"{n.label}: {n.derivation}"
        return Caption(part=stop.part, ref=stop.node, text=text, badge=n.source_class.value)
    if stop.node in checks:
        c = checks[stop.node]
        note = catalog().checks[stop.node].note
        text = f"{c.explanation}, gap {with_unit(c.gap_abs, c.unit)}"
        if note:
            text += f". {note[0].upper()}{note[1:]}"
        return Caption(part=stop.part, ref=stop.node, text=text, badge=c.status)
    return Caption(part=stop.part, ref="", text=stop.caption or stop.node, badge="note")


def _scene_view(data: GeometryScene) -> SceneView:
    graph = catalog_graph()
    all_nodes = {n.id: n for n in graph.nodes}
    all_checks = {c.id: c for c in graph.checks}
    refs = [i for p in data.part for i in (*p.nodes, p.dims_source)]
    refs += [t.node for t in data.tour]
    node_ids = dict.fromkeys(i for i in refs if i in all_nodes)
    check_ids = dict.fromkeys(t.node for t in data.tour if t.node in all_checks)
    return SceneView(
        independence=INDEPENDENCE,
        scene=data,
        source_issues=tuple(validate_geometry_sources(data, catalog())),
        nodes=tuple(all_nodes[i] for i in node_ids),
        checks=tuple(all_checks[i] for i in check_ids),
        captions=tuple(_caption(t, all_nodes, all_checks) for t in data.tour),
    )


@router.get("/catalog", response_model=CatalogIndex)
def get_catalog() -> Response:
    cat = catalog()
    return _json(
        CatalogIndex(
            independence=INDEPENDENCE,
            products=tuple(_summary(cat, stem) for stem in sorted(cat.files)),
        )
    )


@router.get("/catalog/{product}", response_model=ProductView)
def get_product(product: str) -> Response:
    """The product's evaluated graph and physics, with no overrides or hypotheses."""
    return _view(product, InferenceRequest())


@router.post("/inference/{product}", response_model=ProductView)
def post_inference(product: str, request: InferenceRequest) -> Response:
    """Re-evaluate with assumption overrides (SYNTHETIC what-ifs) and at most one hypothesis per
    group. Unknown assumptions or hypotheses, or two alternatives, are 422."""
    return _view(product, request)


@router.get("/geometry", response_model=SceneList)
def list_geometry() -> Response:
    names = tuple(sorted(p.stem for p in GEOMETRY_DIR.glob("*.toml")))
    return _json(SceneList(scenes=names, info=tuple(load_geometry(n).scene for n in names)))


@router.get("/geometry/{scene}", response_model=SceneView)
def get_geometry(scene: str) -> Response:
    try:
        data = load_geometry(scene)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _json(_scene_view(data))


@router.get("/overlay/{scene}", response_model=Overlay)
def get_overlay(
    scene: str,
    mode: Literal["light", "dark"] = "light",
    case: str | None = None,
    isolation_db: float = L20_CASE_ISOLATION_DB,
) -> Response:
    """Light paths with pulse brightness, margins with colors and heater power for a scene
    (model card §3, §13, §14). `case` picks a reference-plane case of the rack and its trays;
    `isolation_db` sets the diplexer isolation of the L20 scenes."""
    try:
        data = load_geometry(scene)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    try:
        result = overlay_for(catalog(), data, mode, case, isolation_db)
    except OverlayError as exc:
        message = str(exc)
        return JSONResponse(
            status_code=422,
            content={
                "detail": message,
                "errors": [{"loc": [], "msg": message, "type": "invalid_input"}],
            },
        )
    if result is None:
        raise HTTPException(status_code=404, detail=f"scene {scene!r} has no overlay")
    return _json(result)
