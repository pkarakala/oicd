"""Reference rack OICD-R64 (model card §14.9). An OICD design, SYNTHETIC: never Lightmatter's.

Space in OpenU (OU), single-tier topology, laser count, the worst optical path evaluated with the
draft IEEE 802.3dj DR budget under the two reference-plane hypotheses, rack yield and the
single-tier radix. Pure functions of a RackSpec; the worst path goes through oicd.report.evaluate.
"""

import math
from statistics import NormalDist
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from oicd.provenance import Provenance, Quantity, SourceClass
from oicd.report import FeasibilityReport, evaluate
from oicd.schema import Link, LossElement
from oicd.units import DB

_FROZEN = ConfigDict(frozen=True, extra="forbid")

ReferencePlane = Literal["H_vclick_channel", "H_vclick_module"]
TrayHeight = Literal["H_2U", "H_1U"]

SYNTHETIC_DESIGN = Provenance(
    source_class=SourceClass.SYNTHETIC,
    rationale="OICD-R64 design choice (model card §14.9), not a Lightmatter configuration.",
)


class PathElement(BaseModel):
    """One element of the worst path. kind 'vclick' moves between channel and module with the
    reference-plane hypothesis; 'fiber' carries a length and is priced at fiber_loss_db_per_km."""

    model_config = _FROZEN

    name: str
    kind: Literal["vclick", "connector", "fiber"]
    loss_db: Quantity[float] | None = None
    length_m: Quantity[float] | None = None


class RackSpec(BaseModel):
    model_config = _FROZEN

    frame_ou: Quantity[int]
    ou_mm: Quantity[float]
    frame_mm: tuple[Quantity[float], Quantity[float], Quantity[float]]  # width, depth, height
    switch_trays: int = Field(ge=1)
    switch_tray_ou: int = Field(ge=1)
    xpu_trays: int = Field(ge=1)
    xpu_tray_ou: dict[TrayHeight, int]
    power_shelves: int = Field(ge=0)
    power_shelf_ou: int = Field(ge=1)
    xpus_per_tray: int = Field(ge=1)
    lanes_per_xpu: int = Field(ge=1)
    switch_lanes: int = Field(ge=1)
    lane_gbps: float = Field(gt=0)
    guide_dr_lanes: int = Field(ge=1)
    worst_path: tuple[PathElement, ...]
    vclick_loss_db: Quantity[float]
    fiber_loss_db_per_km: Quantity[float]
    budget: Link  # the DR budget link; its channel is replaced by the worst path
    link_yields: tuple[float, ...] = (0.9999, 0.99999)
    rack_yield_target: float = Field(default=0.99, gt=0, lt=1)
    ocp_vision_xpus: tuple[int, int] = (1024, 2048)


class Space(BaseModel):
    model_config = _FROZEN

    hypothesis: TrayHeight
    ou_used: int
    ou_available: int
    fits: bool


class PathCase(BaseModel):
    model_config = _FROZEN

    hypothesis: ReferencePlane
    vclick_loss_db: float | None  # None when the vClick sits inside the module
    channel_il_db: float
    report: FeasibilityReport


class YieldRow(BaseModel):
    model_config = _FROZEN

    link_yield: float
    rack_yield: float


class RackResult(BaseModel):
    model_config = _FROZEN

    name: str
    source_class: Literal["synthetic"] = "synthetic"
    space: tuple[Space, ...]
    xpus: int
    links: int
    lanes_per_xpu_per_switch_tray: float
    links_match_switch_capacity: bool
    bidi_fibers: int
    duplex_fibers: int
    tx_lanes: int
    guide_dr_total: float
    guide_dr_per_xpu_tray: float
    guide_dr_per_switch_tray: float
    fiber_m: float
    fiber_db: float
    paths: tuple[PathCase, ...]
    yields: tuple[YieldRow, ...]
    rack_yield_target: float
    link_yield_needed: float
    z_needed: float  # one-sided standard normal quantile of link_yield_needed
    single_tier_xpus: float
    ocp_vision_xpus: tuple[int, int]
    planes_for_vision: tuple[float, float]  # switch planes needed at one lane per XPU per plane


def _q(value: float, provenance: Provenance) -> Quantity[DB]:
    return Quantity(value=DB(value), provenance=provenance)


def _fiber_element(e: PathElement, db_per_km: Quantity[float]) -> tuple[LossElement, float]:
    assert e.length_m is not None
    length = e.length_m
    rationale = (
        f"{length.value:g} m × {db_per_km.value:g} dB/km (length "
        f"{length.provenance.source_class.value}, attenuation "
        f"{db_per_km.provenance.source_class.value})."
    )
    loss = length.value / 1000.0 * db_per_km.value
    provenance = Provenance(source_class=SourceClass.INFERENCE, rationale=rationale)
    return LossElement(name=e.name, loss_max=_q(loss, provenance)), length.value


def _path_link(spec: RackSpec, plane: ReferencePlane, vclick_db: float) -> tuple[Link, float]:
    """The worst path as a §3 link; a vClick is a channel element only under H_vclick_channel."""
    elements: list[LossElement] = []
    fiber_m = 0.0
    for e in spec.worst_path:
        if e.kind == "vclick":
            if plane == "H_vclick_channel":
                q = _q(vclick_db, spec.vclick_loss_db.provenance)
                elements.append(LossElement(name=e.name, loss_max=q))
        elif e.kind == "connector":
            assert e.loss_db is not None
            q = _q(e.loss_db.value, e.loss_db.provenance)
            elements.append(LossElement(name=e.name, loss_max=q))
        else:
            element, length = _fiber_element(e, spec.fiber_loss_db_per_km)
            elements.append(element)
            fiber_m += length
    name = f"OICD-R64 worst path, {plane}"
    link = spec.budget.model_copy(update={"name": name, "channel": tuple(elements)})
    return Link.model_validate(link.model_dump()), fiber_m


def evaluate_rack(spec: RackSpec, name: str = "OICD-R64") -> RackResult:
    space = tuple(
        Space(
            hypothesis=h,
            ou_used=spec.switch_trays * spec.switch_tray_ou
            + spec.xpu_trays * spec.xpu_tray_ou[h]
            + spec.power_shelves * spec.power_shelf_ou,
            ou_available=spec.frame_ou.value,
            fits=spec.switch_trays * spec.switch_tray_ou
            + spec.xpu_trays * spec.xpu_tray_ou[h]
            + spec.power_shelves * spec.power_shelf_ou
            <= spec.frame_ou.value,
        )
        for h in ("H_2U", "H_1U")
    )
    xpus = spec.xpu_trays * spec.xpus_per_tray
    links = xpus * spec.lanes_per_xpu
    tx_lanes = 2 * links
    paths = []
    fiber_m = 0.0
    cases: tuple[tuple[ReferencePlane, float | None], ...] = (
        ("H_vclick_channel", spec.vclick_loss_db.value),
        ("H_vclick_channel", 1.0),
        ("H_vclick_module", None),
    )
    for plane, vclick in cases:
        link, fiber_m = _path_link(spec, plane, vclick if vclick is not None else 0.0)
        report = evaluate(link)
        paths.append(
            PathCase(
                hypothesis=plane,
                vclick_loss_db=vclick,
                channel_il_db=float(report.results[2].evidence["total_loss_db"]),
                report=report,
            )
        )
    needed = spec.rack_yield_target ** (1.0 / links)
    per_plane = spec.lanes_per_xpu / spec.switch_trays
    return RackResult(
        name=name,
        space=space,
        xpus=xpus,
        links=links,
        lanes_per_xpu_per_switch_tray=per_plane,
        links_match_switch_capacity=links == spec.switch_trays * spec.switch_lanes,
        bidi_fibers=links,
        duplex_fibers=2 * links,
        tx_lanes=tx_lanes,
        guide_dr_total=tx_lanes / spec.guide_dr_lanes,
        guide_dr_per_xpu_tray=spec.xpus_per_tray * spec.lanes_per_xpu / spec.guide_dr_lanes,
        guide_dr_per_switch_tray=spec.switch_lanes / spec.guide_dr_lanes,
        fiber_m=fiber_m,
        fiber_db=fiber_m / 1000.0 * spec.fiber_loss_db_per_km.value,
        paths=tuple(paths),
        yields=tuple(YieldRow(link_yield=y, rack_yield=y**links) for y in spec.link_yields),
        rack_yield_target=spec.rack_yield_target,
        link_yield_needed=needed,
        z_needed=NormalDist().inv_cdf(needed),
        single_tier_xpus=spec.switch_lanes / per_plane,
        ocp_vision_xpus=spec.ocp_vision_xpus,
        planes_for_vision=tuple(
            float(math.ceil(n * spec.lanes_per_xpu / spec.switch_lanes))
            for n in spec.ocp_vision_xpus
        ),
    )
