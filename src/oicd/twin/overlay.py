"""Scene overlays for the explorer: light paths, pulses, margins and heater power on scene parts.

Every number comes from the engine's existing physics (model card §3, §12 to §14); this module
only places results on the parts of a catalog/geometry scene. Pulse brightness is the linear
power relative to the scene's reference power (a display scale, 1 at the reference). Light whose
power is not public has power_mw None, a fixed display brightness and no pulses, and its label
says so. Colors come from oicd.display. Pure: the catalog and the scene are passed in.
"""

import math
from collections.abc import Callable, Sequence
from typing import Literal

from pydantic import BaseModel, ConfigDict

from oicd.checks import Status
from oicd.display import Mode, channel_colors, margin_color, palette
from oicd.physics import ring
from oicd.physics.bidi import (
    BidiDirection,
    BidiDirectionResult,
    BidiLinkRequest,
    BidiLinkResult,
    evaluate_bidi_link,
)
from oicd.provenance import Provenance, Quantity, SourceClass
from oicd.report import FeasibilityReport, TracePoint
from oicd.system.rack import PathCase, evaluate_rack
from oicd.twin.catalog import Catalog, GeometryScene
from oicd.twin.inference import evaluate_graph
from oicd.twin.physics import _class, _prov, _value, rack_spec

_FROZEN = ConfigDict(frozen=True, extra="forbid")

INF = SourceClass.INFERENCE
SYN = SourceClass.SYNTHETIC

# Display brightness of light whose power is not public (no number is shown for it).
UNDISCLOSED_BRIGHTNESS = 0.45

# The model card §13.8 BiDi link case: SYNTHETIC diplexers, fiber and connector.
ENGINE_CASE_DIPLEXER_IL_DB = 1.0
ENGINE_CASE_ISOLATION_DB = 25.0
ENGINE_CASE_FIBER_KM = 0.5
ENGINE_CASE_CONNECTOR_DB = 0.5
MAX_ISOLATION_DB = 60.0
_CASE = Provenance(source_class=SYN, rationale="Model card §13.8 BiDi link case (synthetic).")

# The reflected light returns from the fiber interface next to each engine (schematic reach).
GHOST_REACH = 0.18

Direction = Literal["forward", "backward", "none"]


class PathSample(BaseModel):
    """Light just after `label` (an element of the trace) at fraction `at` of the centerline."""

    model_config = _FROZEN

    at: float
    power_mw: float | None
    brightness: float
    label: str


class LightPath(BaseModel):
    model_config = _FROZEN

    part: str
    instances: tuple[int, ...] = ()  # empty: every instance of the part
    kind: Literal["signal", "ghost", "cw"]
    label: str
    color: str
    direction: Direction  # forward runs from the centerline's first point; none: no pulses
    power_kind: Literal["OMA", "AVERAGE"] | None
    samples: tuple[PathSample, ...]
    source_class: SourceClass


class PartValue(BaseModel):
    """A number shown on a part: a margin with its color, or a heater power with its glow."""

    model_config = _FROZEN

    part: str
    label: str
    margin_db: float | None = None
    verdict: Literal["NOT_EXCLUDED", "EXCLUDED"] | None = None
    color: str | None = None
    power_mw: float | None = None
    intensity: float | None = None  # display scale, 0 to 1
    source_class: SourceClass


class OverlayCase(BaseModel):
    model_config = _FROZEN

    id: str
    label: str


class Overlay(BaseModel):
    model_config = _FROZEN

    scene: str
    mode: Mode
    case: str | None
    cases: tuple[OverlayCase, ...]
    legend: str
    reference_mw: float | None  # the power drawn at brightness 1
    reference_kind: Literal["OMA", "AVERAGE"] | None
    verdict: Literal["NOT_EXCLUDED", "EXCLUDED"] | None
    margin_db: float | None
    verdict_note: str = ""  # what decides the verdict, in words
    paths: tuple[LightPath, ...]
    values: tuple[PartValue, ...]
    notes: tuple[str, ...]


Builder = Callable[[Catalog, GeometryScene, Mode, str | None, float], Overlay]


class OverlayError(ValueError):
    """Unknown case or invalid overlay input (422 at the API)."""


def _samples(
    trace: Sequence[TracePoint], reference_mw: float, forward: bool = True
) -> tuple[PathSample, ...]:
    """The trace spread evenly along a centerline (schematic positions), first point first."""
    n = len(trace)
    return tuple(
        PathSample(
            at=(i / (n - 1) if forward else 1.0 - i / (n - 1)) if n > 1 else 0.0,
            power_mw=p.power_mw,
            brightness=p.power_mw / reference_mw,
            label=p.name,
        )
        for i, p in enumerate(trace)
    )


def _steady(
    start: float,
    end: float,
    label: str,
    power_mw: float | None = None,
    reference_mw: float = 1.0,
) -> tuple[PathSample, ...]:
    """Light of one power along a stretch with no losses (or of undisclosed power)."""
    brightness = UNDISCLOSED_BRIGHTNESS if power_mw is None else power_mw / reference_mw
    return tuple(
        PathSample(at=a, power_mw=power_mw, brightness=brightness, label=label)
        for a in (start, end)
    )


def _legend(mode: Mode, extra: str = "") -> str:
    return palette(mode).channel_legend + (f" {extra}" if extra else "")


def _fraction_nearest(path: Sequence[Sequence[float]], point: Sequence[float]) -> float:
    """Arc-length fraction of the centerline point nearest `point` (x and y only)."""
    segments = list(zip(path, path[1:], strict=False))
    lengths = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segments]
    total = sum(lengths)
    best, best_at, walked = math.inf, 0.0, 0.0
    for ((x0, y0, _), (x1, y1, _)), seg in zip(segments, lengths, strict=True):
        t = 0.0
        if seg > 0:
            t = ((point[0] - x0) * (x1 - x0) + (point[1] - y0) * (y1 - y0)) / seg**2
            t = min(max(t, 0.0), 1.0)
        d = math.hypot(x0 + t * (x1 - x0) - point[0], y0 + t * (y1 - y0) - point[1])
        if d < best:
            best, best_at = d, (walked + t * seg) / total
        walked += seg
    return best_at


# --- the BiDi engine-style BiDi pair (model card §13.8) -------------------------------------------


def engine_link_request(
    catalog: Catalog, isolation_db: float = ENGINE_CASE_ISOLATION_DB
) -> BidiLinkRequest:
    """The §13.8 case: BiDi engine wavelengths on the draft DR budget, SYNTHETIC diplexer/fiber."""

    def q(node: str) -> Quantity[float]:
        return Quantity(value=_value(catalog, node), provenance=_prov(catalog, node))

    def syn(value: float) -> Quantity[float]:
        return Quantity(value=value, provenance=_CASE)

    launch = _value(catalog, "ieee3dj.oma_min_intercept") + _value(catalog, "ieee3dj.tdecq_max")
    launch_prov = Provenance(
        source_class=SourceClass.PROPOSED_STANDARD,
        citation_key="johnson2025_3dj_mpidgd",
        rationale="TX OMAouter min −1 + max(TECQ, TDECQ) at TDECQ max (draft, model card §12.1).",
    )

    def direction(name: str, wavelength_node: str) -> BidiDirection:
        return BidiDirection(
            name=name,
            modulation="PAM4",
            symbol_rate_gbd=_value(catalog, "ieee3dj.signaling_rate"),
            tx_oma_dbm=Quantity(value=launch, provenance=launch_prov),
            tx_center_nm=q(wavelength_node),
            tx_tolerance_nm=q("engine.lambda_tolerance_nm"),
            rx_passband_min_nm=q("ieee3dj.lane_wl_min"),
            rx_passband_max_nm=q("ieee3dj.lane_wl_max"),
            rx_sensitivity_dbm=q("ieee3dj.rx_sens_intercept"),
            extra_penalties_db={
                "TDECQ": q("ieee3dj.tdecq_max"),
                "MPI": q("ieee3dj.mpi_allocation"),
            },
        )

    a_nm, b_nm = _value(catalog, "engine.lambda_a_nm"), _value(catalog, "engine.lambda_b_nm")
    isolation = (
        _CASE
        if isolation_db == ENGINE_CASE_ISOLATION_DB
        else Provenance(source_class=SYN, rationale="Diplexer isolation set in the explorer.")
    )
    return BidiLinkRequest(
        name="BiDi engine-style BiDi pair on the draft DR budget (model card §13.8)",
        a_to_b=direction(f"A ({a_nm:g} nm)", "engine.lambda_a_nm"),
        b_to_a=direction(f"B ({b_nm:g} nm)", "engine.lambda_b_nm"),
        diplexer_il_db=syn(ENGINE_CASE_DIPLEXER_IL_DB),
        diplexer_isolation_db=Quantity(value=isolation_db, provenance=isolation),
        fiber_length_km=syn(ENGINE_CASE_FIBER_KM),
        connector_losses_db=(syn(ENGINE_CASE_CONNECTOR_DB),),
        return_loss_db=q("ieee3dj.orl_tolerance_dr1"),
    )


def engine_link(catalog: Catalog, isolation_db: float = ENGINE_CASE_ISOLATION_DB) -> BidiLinkResult:
    if not 0.0 <= isolation_db <= MAX_ISOLATION_DB:
        raise OverlayError(f"diplexer isolation must be 0 to {MAX_ISOLATION_DB:g} dB")
    return evaluate_bidi_link(engine_link_request(catalog, isolation_db))


def _received(part: str, d: BidiDirectionResult, mode: Mode) -> PartValue:
    results = d.report.results
    failed = [r.constraint.value.replace("_", " ") for r in results if r.status is Status.FAIL]
    because = f" ({', '.join(failed)} fails)" if failed else ""
    return PartValue(
        part=part,
        label=f"receives {d.name}: power margin {d.report.margin_db:+.4f} dB; "
        f"{d.report.verdict}{because}",
        margin_db=d.report.margin_db,
        verdict=d.report.verdict,
        color=margin_color(d.report.margin_db, mode),
        source_class=INF,
    )


def _bidi_link(
    catalog: Catalog, scene: GeometryScene, mode: Mode, case: str | None, isolation_db: float
) -> Overlay:
    result = engine_link(catalog, isolation_db)
    a, b = result.directions
    colors = channel_colors(2)
    reference = max(a.report.power_trace[0].power_mw, b.report.power_trace[0].power_mw)

    def ghost(d: BidiDirectionResult, color: str, end: str, forward: bool) -> LightPath:
        span = (1.0 - GHOST_REACH, 1.0) if forward else (GHOST_REACH, 0.0)
        return LightPath(
            part="link.fiber",
            kind="ghost",
            label=f"engine {end}'s own light reflected into its receiver: "
            f"{d.crosstalk_power_mw:.4g} mW",
            color=color,
            direction="forward" if forward else "backward",
            power_kind="OMA",
            samples=tuple(
                PathSample(
                    at=at,
                    power_mw=d.crosstalk_power_mw,
                    brightness=d.crosstalk_power_mw / reference,
                    label="reflected local TX",
                )
                for at in span
            ),
            source_class=INF,
        )

    paths = (
        LightPath(
            part="link.fiber",
            kind="signal",
            label=f"direction {a.name}",
            color=colors[0].color,
            direction="forward",
            power_kind="OMA",
            samples=_samples(a.report.power_trace, reference, forward=True),
            source_class=INF,
        ),
        LightPath(
            part="link.fiber",
            kind="signal",
            label=f"direction {b.name}",
            color=colors[1].color,
            direction="backward",
            power_kind="OMA",
            samples=_samples(b.report.power_trace, reference, forward=False),
            source_class=INF,
        ),
        # direction B is received at end A, next to engine A's transmitter, and vice versa
        ghost(b, colors[0].color, "A", forward=False),
        ghost(a, colors[1].color, "B", forward=True),
    )
    origin = "the SYNTHETIC case value" if isolation_db == ENGINE_CASE_ISOLATION_DB else "set here"
    failing = [
        f"direction {d.name}: {r.constraint.value.replace('_', ' ')} fails"
        for d in (a, b)
        for r in d.report.results
        if r.status is Status.FAIL
    ]
    return Overlay(
        scene=scene.scene.id,
        mode=mode,
        case=None,
        cases=(),
        legend=_legend(mode, "One fiber carries both directions; ghosts are reflections."),
        reference_mw=reference,
        reference_kind="OMA",
        verdict=result.verdict,
        margin_db=result.margin_db,
        verdict_note="; ".join(failing) or "both directions are not excluded",
        paths=paths,
        values=(_received("link.engine_b", a, mode), _received("link.engine_a", b, mode)),
        notes=(
            f"Model card §13.8 case; diplexer isolation {isolation_db:g} dB ({origin}).",
            f"Signal at TP3 {a.report.power_trace[-1].power_mw:.6f} mW; reflected local TX "
            f"{a.crosstalk_power_mw:.4g} mW; reflection crosstalk "
            f"{a.reflection.penalty_db:.6f} dB.",
            "Brightness is linear in power, so a ghost 30 dB or more below the signal is not "
            "visible: lower the isolation to see it.",
        ),
    )


def _engine_package(
    catalog: Catalog, scene: GeometryScene, mode: Mode, case: str | None, isolation_db: float
) -> Overlay:
    result = engine_link(catalog, isolation_db)
    a, b = result.directions
    colors = channel_colors(2)
    reference = a.report.power_trace[0].power_mw
    fiber = next(p for p in scene.part if p.id == "eng.fibers")
    data = tuple(range(32))
    laser = tuple(range(32, fiber.count))
    # in the fiber next to this engine: A after its TX-end diplexer, B before the RX-end one
    out_power = a.report.power_trace[1].power_mw
    in_power = b.report.power_trace[-2].power_mw
    paths = (
        LightPath(
            part="eng.fibers",
            instances=data,
            kind="signal",
            label=f"outbound {a.name}, after the on-chip diplexer",
            color=colors[0].color,
            direction="forward",
            power_kind="OMA",
            samples=_steady(0.0, 1.0, "after TX-end diplexer", out_power, reference),
            source_class=INF,
        ),
        LightPath(
            part="eng.fibers",
            instances=data,
            kind="signal",
            label=f"inbound {b.name}, before the on-chip diplexer",
            color=colors[1].color,
            direction="backward",
            power_kind="OMA",
            samples=_steady(1.0, 0.0, "before RX-end diplexer", in_power, reference),
            source_class=INF,
        ),
        LightPath(
            part="eng.fibers",
            instances=laser,
            kind="cw",
            label="laser supply from the ELSFP (power per fiber not disclosed)",
            color=palette(mode).cw,
            direction="backward",
            power_kind=None,
            samples=_steady(1.0, 0.0, "laser supply"),
            source_class=SourceClass.VENDOR_CLAIM,
        ),
    )
    return Overlay(
        scene=scene.scene.id,
        mode=mode,
        case=None,
        cases=(),
        legend=_legend(mode),
        reference_mw=reference,
        reference_kind="OMA",
        verdict=None,
        margin_db=None,
        paths=paths,
        values=(),
        notes=("Signal powers from the model card §13.8 case (draft DR budget, SYNTHETIC parts).",),
    )


# --- the reference rack and its trays (model card §14.9) ----------------------------------


def _rack_cases(catalog: Catalog) -> list[tuple[OverlayCase, PathCase]]:
    result = evaluate_rack(rack_spec(catalog))
    out = []
    for p in result.paths:
        if p.fau_loss_db is None:
            case = OverlayCase(id=p.hypothesis, label="FAU inside the module (H_fau_module)")
        else:
            case = OverlayCase(
                id=f"{p.hypothesis}_{p.fau_loss_db:.1f}".replace(".", "p"),
                label=f"FAU {p.fau_loss_db:g} dB in the channel ({p.hypothesis})",
            )
        out.append((case, p))
    return out


def _pick_case(
    cases: list[tuple[OverlayCase, PathCase]], case: str | None
) -> tuple[OverlayCase, PathCase]:
    if case is None:
        return cases[0]
    for c in cases:
        if c[0].id == case:
            return c
    raise OverlayError(f"unknown case {case!r}; cases: {', '.join(c[0].id for c in cases)}")


def _split(trace: Sequence[TracePoint]) -> tuple[list[TracePoint], list[TracePoint]]:
    """The XPU-tray part of the worst path (to the blind mate) and the switch-tray part."""
    names = [p.name for p in trace]
    xpu_end = names.index("PRIZM TMT blind mate") + 1
    switch_start = names.index("switch-tray connector")
    return list(trace[:xpu_end]), list(trace[switch_start:])


def _margin_value(part: str, label: str, report: FeasibilityReport, mode: Mode) -> PartValue:
    return PartValue(
        part=part,
        label=label,
        margin_db=report.margin_db,
        verdict=report.verdict,
        color=margin_color(report.margin_db, mode),
        source_class=INF,
    )


def _rack(
    catalog: Catalog, scene: GeometryScene, mode: Mode, case: str | None, isolation_db: float
) -> Overlay:
    cases = _rack_cases(catalog)
    chosen, path = _pick_case(cases, case)
    report = path.report
    trace = report.power_trace
    reference = trace[0].power_mw
    colors = channel_colors(2)
    a_nm = _value(catalog, "els_dr.lambda_range_a")
    b_nm = _value(catalog, "els_dr.lambda_range_b")
    paths: list[LightPath] = []
    for part in ("rack.shuffle_low", "rack.shuffle_high"):
        paths += [
            LightPath(
                part=part,
                kind="signal",
                label=f"direction A ({a_nm:g} nm), XPU to switch",
                color=colors[0].color,
                direction="forward",
                power_kind="OMA",
                samples=_samples(trace, reference, forward=True),
                source_class=INF,
            ),
            LightPath(
                part=part,
                kind="signal",
                label=f"direction B ({b_nm:g} nm), switch to XPU",
                color=colors[1].color,
                direction="backward",
                power_kind="OMA",
                samples=_samples(trace, reference, forward=False),
                source_class=INF,
            ),
        ]
    label = f"worst path {report.margin_db:+.4f} dB, {report.verdict} ({chosen.label})"
    parts = ("rack.shuffle_low", "rack.shuffle_high")  # the margin colors the carriers only
    return Overlay(
        scene=scene.scene.id,
        mode=mode,
        case=chosen.id,
        cases=tuple(c for c, _ in cases),
        legend=_legend(mode),
        reference_mw=reference,
        reference_kind="OMA",
        verdict=report.verdict,
        margin_db=report.margin_db,
        verdict_note=f"worst path on the draft DR budget, {chosen.label}",
        paths=tuple(paths),
        values=tuple(_margin_value(p, label, report, mode) for p in parts),
        notes=(
            "OICD-R64 is an OICD design (SYNTHETIC), not a vendor configuration.",
            "The reference-plane definition, not the physics, decides this rack (model card "
            "§14.9).",
        ),
    )


def _tray(engines: str, ribbons: tuple[str, str], transmits_a: bool) -> Builder:
    def build(
        catalog: Catalog, scene: GeometryScene, mode: Mode, case: str | None, isolation_db: float
    ) -> Overlay:
        cases = _rack_cases(catalog)
        chosen, path = _pick_case(cases, case)
        report = path.report
        out_trace, in_trace = _split(report.power_trace)
        reference = report.power_trace[0].power_mw
        a, b = channel_colors(2)
        a_nm = _value(catalog, "els_dr.lambda_range_a")
        b_nm = _value(catalog, "els_dr.lambda_range_b")
        (out_c, out_nm), (in_c, in_nm) = (
            ((a, a_nm), (b, b_nm)) if transmits_a else ((b, b_nm), (a, a_nm))
        )
        paths: list[LightPath] = []
        for part in ribbons:
            paths += [
                LightPath(
                    part=part,
                    kind="signal",
                    label=f"outbound ({out_nm:g} nm) to the rear blind mate",
                    color=out_c.color,
                    direction="forward",
                    power_kind="OMA",
                    samples=_samples(out_trace, reference, forward=True),
                    source_class=INF,
                ),
                LightPath(
                    part=part,
                    kind="signal",
                    label=f"inbound ({in_nm:g} nm) from the rear blind mate",
                    color=in_c.color,
                    direction="backward",
                    power_kind="OMA",
                    samples=_samples(in_trace, reference, forward=False),
                    source_class=INF,
                ),
            ]
        label = f"rack worst path {report.margin_db:+.4f} dB, {report.verdict} ({chosen.label})"
        return Overlay(
            scene=scene.scene.id,
            mode=mode,
            case=chosen.id,
            cases=tuple(c for c, _ in cases),
            legend=_legend(mode),
            reference_mw=reference,
            reference_kind="OMA",
            verdict=report.verdict,
            margin_db=report.margin_db,
            verdict_note=f"the reference rack's worst path, {chosen.label}",
            paths=tuple(paths),
            values=(_margin_value(engines, label, report, mode),),
            notes=(
                "Pulses show the in-tray part of the reference rack's worst path (model card "
                "§14.9); the tray layout is SCHEMATIC.",
            ),
        )

    return build


# --- PIC region, ring section, lasers and the WDM packages ---------------------------------


def _heater(catalog: Catalog, part: str) -> PartValue:
    """Worst-case heater power with barrel shifting: one WDM spacing (model card §13.4)."""
    eta = _value(catalog, "ring.heater_nm_per_mw")
    spacing = _value(catalog, "ring.wdm_compat_spacing_ghz")
    fsr = _value(catalog, "ring.fsr_thz") * 1000.0
    worst = ring.heater_power_mw(ring.span_nm(spacing, 1310.0), eta)
    full = ring.heater_power_mw(ring.span_nm(fsr, 1310.0), eta)
    return PartValue(
        part=part,
        label=f"heater ≤ {worst:.4f} mW with barrel shifting (one {spacing:g} GHz spacing); "
        f"{full:.4f} mW for a full FSR",
        power_mw=worst,
        intensity=worst / full,
        source_class=INF,
    )


def _pic_region(
    catalog: Catalog, scene: GeometryScene, mode: Mode, case: str | None, isolation_db: float
) -> Overlay:
    parts = {p.id: p for p in scene.part}
    a, b = channel_colors(2)
    tx_path, rx_path = parts["pic.tx_bus"].path, parts["pic.rx_bus"].path
    at_mrm = _fraction_nearest(tx_path, parts["pic.mrm"].position)
    at_mrr = _fraction_nearest(rx_path, parts["pic.mrr"].position)
    note = "(representative lane; powers not disclosed)"
    paths = (
        LightPath(
            part="pic.tx_bus",
            kind="cw",
            label=f"laser supply to the modulator {note}",
            color=palette(mode).cw,
            direction="backward",
            power_kind=None,
            samples=_steady(1.0, at_mrm, "laser input coupler"),
            source_class=SYN,
        ),
        LightPath(
            part="pic.tx_bus",
            kind="signal",
            label=f"modulated transmit light (direction A) {note}",
            color=a.color,
            direction="backward",
            power_kind=None,
            samples=_steady(at_mrm, 0.0, "ring modulator"),
            source_class=SYN,
        ),
        LightPath(
            part="pic.fiber_bus",
            kind="signal",
            label=f"transmit light to the fiber {note}",
            color=a.color,
            direction="backward",
            power_kind=None,
            samples=_steady(1.0, 0.0, "diplexer"),
            source_class=SYN,
        ),
        LightPath(
            part="pic.fiber_bus",
            kind="signal",
            label=f"receive light from the fiber (direction B) {note}",
            color=b.color,
            direction="forward",
            power_kind=None,
            samples=_steady(0.0, 1.0, "fiber coupler"),
            source_class=SYN,
        ),
        LightPath(
            part="pic.rx_bus",
            kind="signal",
            label=f"receive light to the ring filter {note}",
            color=b.color,
            direction="forward",
            power_kind=None,
            samples=_steady(0.0, at_mrr, "diplexer"),
            source_class=SYN,
        ),
        LightPath(
            part="pic.drop_bus",
            kind="signal",
            label=f"dropped channel to the photodiode {note}",
            color=b.color,
            direction="forward",
            power_kind=None,
            samples=_steady(0.0, 1.0, "receive ring"),
            source_class=SYN,
        ),
    )
    return Overlay(
        scene=scene.scene.id,
        mode=mode,
        case=None,
        cases=(),
        legend=_legend(mode),
        reference_mw=None,
        reference_kind=None,
        verdict=None,
        margin_db=None,
        paths=paths,
        values=(_heater(catalog, "pic.mrm_heater"), _heater(catalog, "pic.mrr_heater")),
        notes=("Heater power: model card §13.4 at 0.44 nm/mW (vendor_ofc25_paper), INFERENCE.",),
    )


def _ring_section(
    catalog: Catalog, scene: GeometryScene, mode: Mode, case: str | None, isolation_db: float
) -> Overlay:
    return Overlay(
        scene=scene.scene.id,
        mode=mode,
        case=None,
        cases=(),
        legend="",
        reference_mw=None,
        reference_kind=None,
        verdict=None,
        margin_db=None,
        paths=(),
        values=(_heater(catalog, "rs.heater"),),
        notes=("Heater power: model card §13.4 at 0.44 nm/mW (vendor_ofc25_paper), INFERENCE.",),
    )


def _lasers(
    catalog: Catalog, scene: GeometryScene, mode: Mode, case: str | None, isolation_db: float
) -> Overlay:
    cw = palette(mode).cw
    dr_mw = _value(catalog, "els_dr.power_per_fiber")
    g1_count = _value(catalog, "els_dwdm.wavelengths_per_fiber")
    g1_lambda_mw = _value(catalog, "els_dwdm.power_per_lambda")
    g1_mw = g1_count * g1_lambda_mw  # model card §14.6: 8 × 13 mW = 104 mW
    guide_mw = _value(catalog, "els.power_per_fiber_yole")
    lasers = _value(catalog, "els_dr.lasers_per_module")

    def supply(part: str, label: str, power: float, cls: SourceClass) -> LightPath:
        # brightness relative to the ELS-DR's 200 mW per fiber
        return LightPath(
            part=part,
            kind="cw",
            label=label,
            color=cw,
            direction="forward",
            power_kind="AVERAGE",
            samples=_steady(0.0, 1.0, "laser output", power, dr_mw),
            source_class=cls,
        )

    return Overlay(
        scene=scene.scene.id,
        mode=mode,
        case=None,
        cases=(),
        legend="Unmodulated laser supply, average power (false color; O-band light is invisible).",
        reference_mw=dr_mw,
        reference_kind="AVERAGE",
        verdict=None,
        margin_db=None,
        paths=(
            supply(
                "elsdr.ribbons",
                f"ELS-DR: 8 fibers per ribbon at {dr_mw:g} mW each",
                dr_mw,
                _class(catalog, "els_dr.power_per_fiber"),
            ),
            supply(
                "elsdwdm.fibers",
                f"ELS-DWDM: {g1_count:g} wavelengths at {g1_lambda_mw:g} mW = {g1_mw:g} mW "
                "per fiber",
                g1_mw,
                INF,
            ),
            supply(
                "els.fibers",
                f"ELS: {guide_mw:g} mW per fiber",
                guide_mw,
                _class(catalog, "els.power_per_fiber_yole"),
            ),
        ),
        values=(
            PartValue(
                part="elsdr.laser_pic",
                label=f"{lasers:g} lasers × {dr_mw:g} mW = {lasers * dr_mw / 1000:g} W optical",
                power_mw=lasers * dr_mw,
                source_class=INF,
            ),
        ),
        notes=("Powers are CW average power per fiber, never OMA.",),
    )


def _undisclosed(parts: tuple[str, ...], label: str) -> Builder:
    def build(
        catalog: Catalog, scene: GeometryScene, mode: Mode, case: str | None, isolation_db: float
    ) -> Overlay:
        a = channel_colors(2)[0]
        return Overlay(
            scene=scene.scene.id,
            mode=mode,
            case=None,
            cases=(),
            legend=_legend(mode),
            reference_mw=None,
            reference_kind=None,
            verdict=None,
            margin_db=None,
            paths=tuple(
                LightPath(
                    part=part,
                    kind="signal",
                    label=label,
                    color=a.color,
                    direction="none",
                    power_kind=None,
                    samples=_steady(0.0, 1.0, "fiber"),
                    source_class=SourceClass.VENDOR_CLAIM,
                )
                for part in parts
            ),
            values=(),
            notes=("Optical powers are not disclosed, so no pulses are drawn.",),
        )

    return build


def _processor(
    catalog: Catalog, scene: GeometryScene, mode: Mode, case: str | None, isolation_db: float
) -> Overlay:
    """Laser supply into the processor and the optical power per weight cell (§15.5)."""
    per_fibre = _value(catalog, "ptc.laser_power_fibre")
    eta = evaluate_graph(catalog, "photonic_processor", hypotheses=("H_lasers_dedicated",))
    cell = next(n for n in eta.nodes if n.id == "ptc.power_per_cell")
    assert cell.nominal is not None
    return Overlay(
        scene=scene.scene.id,
        mode=mode,
        case=None,
        cases=(),
        legend="Unmodulated laser supply, average power in fibre (false color).",
        reference_mw=per_fibre,
        reference_kind="AVERAGE",
        verdict=None,
        margin_db=None,
        paths=(
            LightPath(
                part="proc.fibres",
                kind="cw",
                label=f"8 lasers at {per_fibre:g} mW in fibre (unverified; CWDM grid; mapping to "
                "cores not disclosed)",
                color=palette(mode).cw,
                direction="forward",
                power_kind="AVERAGE",
                samples=_steady(0.0, 1.0, "laser output", per_fibre, per_fibre),
                source_class=_class(catalog, "ptc.laser_power_fibre"),
            ),
        ),
        values=(
            PartValue(
                part="proc.weights",
                label=f"{cell.nominal:.4g} µW per weight cell under H_lasers_dedicated "
                "(model card §15.5)",
                power_mw=cell.nominal / 1000.0,
                source_class=INF,
            ),
        ),
        notes=("Per-cell power: 1.6 W after the fibre-to-cell losses, shared by 65,536 cells.",),
    )


BUILDERS: dict[str, Builder] = {
    "reference_rack": _rack,
    "switch_tray": _tray("sw.engines", ("sw.ribbons_left", "sw.ribbons_right"), False),
    "xpu_tray": _tray("xpu.engines", ("xpu.fibers_left", "xpu.fibers_right"), True),
    "bidi_engine": _engine_package,
    "bidi_link": _bidi_link,
    "pic_region": _pic_region,
    "ring_section": _ring_section,
    "laser_sources": _lasers,
    "photonic_interposer": _undisclosed(
        ("pi.fibers_left", "pi.fibers_right"),
        "8 wavelengths per fiber at 56 Gb/s NRZ (direction and power not disclosed)",
    ),
    "photonic_processor": _processor,
    "cpo_chiplet": _undisclosed(
        ("cpog.fibers",), "16 wavelengths per fiber (direction and power not disclosed)"
    ),
}


def overlay_for(
    catalog: Catalog,
    scene: GeometryScene,
    mode: Mode = "light",
    case: str | None = None,
    isolation_db: float = ENGINE_CASE_ISOLATION_DB,
) -> Overlay | None:
    """The overlay of a scene, or None when the scene has none."""
    build = BUILDERS.get(scene.scene.id)
    return None if build is None else build(catalog, scene, mode, case, isolation_db)
