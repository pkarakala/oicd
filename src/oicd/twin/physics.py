"""Physics evaluations attached to the product twins (model card §13, §14).

Each product's evaluation runs the engine (oicd.physics, oicd.upstream, oicd.report, oicd.system)
on catalog values, so every number carries its class: facts keep theirs, assumptions are
SYNTHETIC and computed results are INFERENCE. Pure: the catalog is passed in, nothing is read.
"""

import math
from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel, ConfigDict

from oicd.checks.wavelength import clearances_nm
from oicd.physics import ring, wdm
from oicd.physics.mpi import mpi_penalty_db
from oicd.provenance import Provenance, Quantity, SourceClass
from oicd.report import evaluate
from oicd.schema import (
    FEC,
    ElectricalInterface,
    Link,
    LossElement,
    Penalty,
    Receiver,
    Transmitter,
    UpstreamChain,
)
from oicd.system.pod import PodSpec, evaluate_pod
from oicd.system.rack import PathElement, RackSpec, evaluate_rack
from oicd.twin.catalog import Assumption, Catalog, Fact
from oicd.units import DB, DBm, OpticalPower, PowerKind
from oicd.upstream import derive_tp2, max_fanout

_FROZEN = ConfigDict(frozen=True, extra="forbid")

INF = SourceClass.INFERENCE
SYN = SourceClass.SYNTHETIC

# Silicon thermo-optic coefficient at 1.3 µm and 295 K (frey2006_dndt, Table 4).
SI_DN_DT_PER_K = 1.94e-4
SI_DN_DT = Provenance(
    source_class=SourceClass.PEER_REVIEWED,
    citation_key="frey2006_dndt",
    rationale="Silicon dn/dT = 1.94E-04 /K at 1.3 microns and 295 K (Table 4).",
)
# Model card §10 chain (all SYNTHETIC), used for the Guide DR fan-out of §14.6.
CHAIN_DB = {
    "laser_fiber_loss": 0.5,
    "coupling_loss": 1.5,
    "excess_loss": 0.0,
    "modulator_il": 4.0,
    "output_coupler_loss": 1.5,
    "extinction_ratio": 4.0,
}
CHAIN = Provenance(source_class=SYN, rationale="Model card §10 chain loss (synthetic).")


class Item(BaseModel):
    model_config = _FROZEN

    label: str
    value: float | str | None
    unit: str
    source_class: SourceClass
    note: str = ""


class Section(BaseModel):
    model_config = _FROZEN

    title: str
    hypothesis: str | None = None
    items: tuple[Item, ...]
    verdict: Literal["NOT_EXCLUDED", "EXCLUDED"] | None = None
    note: str = ""


class ProductPhysics(BaseModel):
    model_config = _FROZEN

    product: str
    sections: tuple[Section, ...]


def _value(catalog: Catalog, node_id: str, pins: dict[str, float] | None = None) -> float:
    if pins and node_id in pins:
        return pins[node_id]
    node = catalog.nodes[node_id]
    if isinstance(node, Assumption):
        return node.nominal
    if isinstance(node, Fact):
        return node.nominal
    raise KeyError(f"{node_id} is a derived node; physics reads facts and assumptions")


def _prov(catalog: Catalog, node_id: str) -> Provenance:
    node = catalog.nodes[node_id]
    if isinstance(node, Fact):
        return (
            Provenance(
                source_class=node.source_class,
                citation_key=node.cite if node.verified else None,
                rationale=f"{node.quantity} ({node_id}): {node.quote}",
            )
            if node.verified
            else Provenance(source_class=SYN, rationale=f"{node_id} (unverified)")
        )
    assert isinstance(node, Assumption)
    return Provenance(source_class=SYN, rationale=f"{node_id}: {node.rationale}")


def _class(catalog: Catalog, node_id: str) -> SourceClass:
    node = catalog.nodes[node_id]
    return node.source_class if isinstance(node, Fact) else SYN


def dr_budget_link(catalog: Catalog, name: str = "draft 802.3dj DR budget") -> Link:
    """The model card §12.1 DR link, built from the catalog's draft 802.3dj facts."""

    def q(value: float, node_id: str) -> Quantity:
        return Quantity(value=value, provenance=_prov(catalog, node_id))

    electrical = ElectricalInterface(
        modulation="PAM4",
        symbol_rate_gbd=_value(catalog, "ieee3dj.signaling_rate"),
        lanes=1,
        fec=FEC.RS_544_514,
        provenance=_prov(catalog, "ieee3dj.signaling_rate"),
    )
    lo, hi = _value(catalog, "ieee3dj.lane_wl_min"), _value(catalog, "ieee3dj.lane_wl_max")
    launch = _value(catalog, "ieee3dj.oma_min_intercept") + _value(catalog, "ieee3dj.tdecq_max")
    launch_prov = Provenance(
        source_class=SourceClass.PROPOSED_STANDARD,
        citation_key="johnson2025_3dj_mpidgd",
        rationale="TX OMAouter min −1 + max(TECQ, TDECQ) at TDECQ max (draft, model card §12.1).",
    )
    return Link(
        name=name,
        tx=Transmitter(
            name="draft DR TX",
            electrical=electrical,
            center_wavelength_nm=q((lo + hi) / 2.0, "ieee3dj.lane_wl_min"),
            wavelength_tolerance_nm=q((hi - lo) / 2.0, "ieee3dj.lane_wl_max"),
            launch_oma_min=Quantity(
                value=OpticalPower(DBm(launch), PowerKind.OMA), provenance=launch_prov
            ),
        ),
        rx=Receiver(
            name="draft DR RX",
            electrical=electrical,
            passband_min_nm=q(lo, "ieee3dj.lane_wl_min"),
            passband_max_nm=q(hi, "ieee3dj.lane_wl_max"),
            sensitivity_oma_max=Quantity(
                value=OpticalPower(
                    DBm(_value(catalog, "ieee3dj.rx_sens_intercept")), PowerKind.OMA
                ),
                provenance=_prov(catalog, "ieee3dj.rx_sens_intercept"),
            ),
        ),
        channel=(
            LossElement(
                name="channel insertion loss (max)",
                loss_max=Quantity(
                    value=DB(_value(catalog, "ieee3dj.channel_il")),
                    provenance=_prov(catalog, "ieee3dj.channel_il"),
                ),
            ),
        ),
        penalties=tuple(
            Penalty(
                name=name,
                value=Quantity(value=DB(_value(catalog, node)), provenance=_prov(catalog, node)),
            )
            for name, node in (
                ("TDECQ", "ieee3dj.tdecq_max"),
                ("MPI", "ieee3dj.mpi_allocation"),
                ("DGD", "ieee3dj.dgd_allocation"),
            )
        ),
        reserve=Quantity(
            value=DB(0.0),
            provenance=Provenance(
                source_class=SYN, rationale="The draft budget leaves no reserve."
            ),
        ),
    )


def _l20(catalog: Catalog) -> tuple[Section, ...]:
    delta = _value(catalog, "l20.lambda_tolerance_nm")
    lo, hi = _value(catalog, "ieee3dj.lane_wl_min"), _value(catalog, "ieee3dj.lane_wl_max")
    items = []
    contained_all = True
    for label, node in (("direction A", "l20.lambda_a_nm"), ("direction B", "l20.lambda_b_nm")):
        center = _value(catalog, node)
        lower, upper, ok = clearances_nm(center, delta, lo, hi)
        contained_all &= ok
        items += [
            Item(
                label=f"{label} at {center:g} nm: lower clearance",
                value=lower,
                unit="nm",
                source_class=INF,
            ),
            Item(
                label=f"{label} at {center:g} nm: upper clearance",
                value=upper,
                unit="nm",
                source_class=INF,
            ),
            Item(
                label=f"{label}: inside the draft DR range",
                value="yes" if ok else "no",
                unit="",
                source_class=INF,
            ),
        ]
    return (
        Section(
            title=f"Draft IEEE 802.3dj DR wavelength range {lo:g} to {hi:g} nm, δ = {delta:g} nm",
            items=tuple(items),
            verdict="NOT_EXCLUDED" if contained_all else "EXCLUDED",
            note="'DR compatible' cannot mean draft-DR wavelength compliance in both directions "
            "(open question, INFERENCE; model card §14.2).",
        ),
    )


def _windows(catalog: Catalog, q: float, f0: float, rates: tuple[float, ...]) -> Section:
    items = []
    for baud in rates:
        for spacing in (200.0, 400.0):
            w = ring.design_window(f0, spacing, baud, q=q)
            items.append(
                Item(
                    label=f"{baud:g} GBd at {spacing:g} GHz: Q window",
                    value=f"[{w.q_min:.1f}, {w.q_max:.1f}] {'open' if w.open else 'closed'}; "
                    f"Q {q:g} {'inside' if w.q_inside else 'outside'}",
                    unit="",
                    source_class=INF,
                )
            )
    return Section(
        title="Design windows (SYNTHETIC rules: −15 dB per neighbor, f0/Q ≥ 0.75 × symbol rate)",
        items=tuple(items),
        note="Model card §13.3.",
    )


def _ring_ofc25(catalog: Catalog) -> tuple[Section, ...]:
    q = _value(catalog, "ring.mrm_q")
    fsr_ghz = _value(catalog, "ring.fsr_thz") * 1000.0
    diameter = _value(catalog, "m1000.mrr_diameter")
    s = ring.ring_summary(1310.0, q, fsr_ghz_value=fsr_ghz, diameter_um=diameter)
    params = Section(
        title="Ring at 1310 nm (Q and FSR from the OFC 2025 talk and paper)",
        items=(
            Item(label="f0", value=s.f0_ghz / 1000.0, unit="THz", source_class=INF),
            Item(label="FWHM = f0/Q_L", value=s.fwhm_ghz, unit="GHz", source_class=INF),
            Item(label="FWHM", value=s.fwhm_nm, unit="nm", source_class=INF),
            Item(label="FSR", value=s.fsr_nm, unit="nm", source_class=INF),
            Item(
                label="FSR in 200 GHz slots", value=fsr_ghz / 200.0, unit="slots", source_class=INF
            ),
            Item(
                label="implied group index for a ~15 µm diameter (M1000 slide)",
                value=s.group_index,
                unit="",
                source_class=INF,
                note="cross-source INFERENCE: the OFC 2025 FSR with the M1000 ring diameter",
            ),
            Item(
                label="one neighbor at 200 GHz",
                value=s.neighbor_rejection_db["200"],
                unit="dB",
                source_class=INF,
            ),
            Item(
                label="one neighbor at 400 GHz",
                value=s.neighbor_rejection_db["400"],
                unit="dB",
                source_class=INF,
            ),
            Item(
                label="heater power per 200 GHz of tuning",
                value=ring.heater_power_mw(
                    ring.span_nm(200.0, 1310.0), _value(catalog, "ring.heater_nm_per_mw")
                ),
                unit="mW",
                source_class=INF,
            ),
        ),
        note="Model card §13.1 and §13.8.",
    )
    return params, _windows(catalog, q, s.f0_ghz, (56.0, 106.25))


def _m1000(catalog: Catalog) -> tuple[Section, ...]:
    q = _value(catalog, "ring.mrm_q")
    f0 = ring.resonance_frequency_ghz(1310.0)
    spacing = _value(catalog, "ring.wdm_compat_spacing_ghz")
    window = ring.design_window(f0, spacing, _value(catalog, "m1000.lane_rate_nrz"), q=q)
    ng = ring.group_index_from_fsr(
        _value(catalog, "ring.fsr_thz") * 1000.0,
        ring.circumference_um(_value(catalog, "m1000.mrr_diameter")),
    )
    drift = ring.thermal_drift_nm_per_k(1310.0, SI_DN_DT_PER_K, ng)
    sections = [
        Section(
            title="M1000 ring window, assuming the OFC 2025 rings (Q 3500, 200 GHz, 56 Gb/s NRZ)",
            items=(
                Item(
                    label="Q_min (−15 dB per neighbor)",
                    value=window.q_min,
                    unit="",
                    source_class=INF,
                ),
                Item(
                    label="Q_max (f0/Q ≥ 0.75 × 56 GBd)",
                    value=window.q_max,
                    unit="",
                    source_class=INF,
                ),
                Item(
                    label="window",
                    value="open" if window.open else "closed",
                    unit="",
                    source_class=INF,
                ),
                Item(
                    label="Q 3500 inside",
                    value="yes" if window.q_inside else "no",
                    unit="",
                    source_class=INF,
                ),
            ),
            note="INFERENCE: the M1000 ring parameters are not disclosed "
            "(model card §13.3, §14.3).",
        )
    ]
    for barrel in (True, False):
        t = ring.thermal_tuning(
            1310.0,
            laser_accuracy_ghz=20.0,
            fabrication_offset_nm=1.0,
            drift_nm_per_k=drift,
            temperature_swing_k=10.0,
            spacing_ghz=spacing,
            fsr_ghz=_value(catalog, "ring.fsr_thz") * 1000.0,
            efficiency_nm_per_mw=_value(catalog, "ring.heater_nm_per_mw"),
            barrel_shifting=barrel,
        )
        sections.append(
            Section(
                title="Thermal tuning per ring "
                + ("with" if barrel else "without")
                + " barrel shifting",
                items=(
                    Item(
                        label="laser accuracy ±20 GHz",
                        value=t.laser_accuracy_nm,
                        unit="nm",
                        source_class=INF,
                    ),
                    Item(
                        label="fabrication offset",
                        value=t.fabrication_offset_nm,
                        unit="nm",
                        source_class=SYN,
                    ),
                    Item(
                        label="drift over a 10 K swing (dλ/dT, mode in silicon)",
                        value=t.drift_nm,
                        unit="nm",
                        source_class=INF,
                        note=f"dn/dT 1.94e-4 /K (frey2006_dndt), n_g {ng:.4f} (INFERENCE)",
                    ),
                    Item(label="required tuning", value=t.required_nm, unit="nm", source_class=INF),
                    Item(
                        label="worst-case range",
                        value=t.worst_case_range_nm,
                        unit="nm",
                        source_class=INF,
                    ),
                    Item(
                        label="heater power for the worst-case range",
                        value=t.heater_power_mw,
                        unit="mW",
                        source_class=INF,
                    ),
                    Item(
                        label="2048 rings at that power",
                        value=t.heater_power_mw
                        * _value(catalog, "m1000.fiber_count")
                        * _value(catalog, "m1000.wdm_lambda")
                        / 1000.0,
                        unit="W",
                        source_class=INF,
                    ),
                ),
                note="Model card §13.4; the 10 K swing and ±1 nm offset are SYNTHETIC.",
            )
        )
    return tuple(sections)


def _bidi16(catalog: Catalog) -> tuple[Section, ...]:
    count = int(_value(catalog, "bidi16.lambda_count"))
    grid = wdm.interleaved_grid(
        _value(catalog, "bidi16.center_nm"), _value(catalog, "bidi16.txrx_spacing_ghz"), count
    )
    q = _value(catalog, "ring.mrm_q")
    fwhm = ring.fwhm_ghz(ring.resonance_frequency_ghz(_value(catalog, "bidi16.center_nm")), q)
    il = _value(catalog, "bidi16.channel_loss")
    rl = _value(catalog, "bidi16.return_loss_db")
    mpi = mpi_penalty_db(
        2,
        _value(catalog, "bidi16.mpi_er_db"),
        _value(catalog, "bidi16.mpi_rt_db"),
        _value(catalog, "bidi16.mpi_rr_db"),
        _value(catalog, "bidi16.mpi_rc_db"),
        int(_value(catalog, "bidi16.connector_count")),
    ).penalty_db
    s_rx = _value(catalog, "ring.oma_min_dbm")
    receive, transmit = range(1, count, 2), range(0, count, 2)
    t400 = ring.lorentzian(400.0, fwhm)
    t200 = ring.lorentzian(200.0, fwhm)
    sections = [
        Section(
            title="Interleaving (single Lorentzian, images excluded)",
            items=(
                Item(
                    label="one neighbor at 400 GHz",
                    value=ring.db(t400),
                    unit="dB",
                    source_class=INF,
                ),
                Item(
                    label="one neighbor at 200 GHz",
                    value=ring.db(t200),
                    unit="dB",
                    source_class=INF,
                ),
                Item(
                    label="isolation gained by interleaving",
                    value=ring.db(t200 / t400),
                    unit="dB",
                    source_class=INF,
                ),
            ),
            note="Model card §13.8.",
        )
    ]
    for h_id in ("H_fsr18", "H_fsr32"):
        fsr_ghz = catalog.hypotheses[h_id].sets["bidi16.ring_fsr_thz"] * 1000.0
        rings = [
            wdm.ring_leakage(grid, n, fwhm, fsr_ghz, receive, transmit, "NRZ", il, rl)
            for n in receive
        ]
        worst = wdm.worst_channel(grid, rings)
        aliased = [r.channel for r in rings if any(i.direction == "counter" for i in r.images)]
        assert worst.reflection_db is not None
        min_tx = s_rx + il + worst.crosstalk_db + worst.reflection_db + mpi
        sections.append(
            Section(
                title=f"Worst receive channel, FSR {fsr_ghz / 1000:g} THz",
                hypothesis=h_id,
                items=(
                    Item(
                        label="worst receive channel",
                        value=float(worst.channel),
                        unit="",
                        source_class=INF,
                    ),
                    Item(
                        label="co-directional leakage X",
                        value=worst.leakage,
                        unit="",
                        source_class=INF,
                    ),
                    Item(
                        label="crosstalk penalty, NRZ",
                        value=worst.crosstalk_db,
                        unit="dB",
                        source_class=INF,
                    ),
                    Item(
                        label="reflected local-transmitter leakage X_r",
                        value=worst.reflected_leakage,
                        unit="",
                        source_class=INF,
                    ),
                    Item(
                        label="reflection crosstalk",
                        value=worst.reflection_db,
                        unit="dB",
                        source_class=INF,
                    ),
                    Item(
                        label="MPI bound (NRZ, ER 6 dB, Rt = Rr = −26, Rc = −45 dB, n = 6)",
                        value=mpi,
                        unit="dB",
                        source_class=INF,
                    ),
                    Item(
                        label="minimum TX OMA = S_RX + IL + penalties",
                        value=min_tx,
                        unit="dBm",
                        source_class=INF,
                        note="S_RX −9 dBm OMA from the OFC 2025 talk (cross-source assumption)",
                    ),
                    Item(
                        label="receive rings with an image on a local transmitter",
                        value=", ".join(str(c) for c in aliased) or "none",
                        unit="",
                        source_class=INF,
                    ),
                ),
                note="Model card §13.6 and §14.5; TX OMA is not public. BER < 1e-9 without "
                "FEC stays a VENDOR_CLAIM, not something OICD checks.",
            )
        )
    return tuple(sections)


def _chain_link(catalog: Catalog, laser_mw: float, n: int) -> Link:
    base = dr_budget_link(catalog, "Guide DR fan-out on the draft DR budget")

    def q(value: object) -> Quantity:
        return Quantity(value=value, provenance=CHAIN)

    chain = UpstreamChain(
        name="model card §10 chain from one Guide DR fiber",
        laser_power_avg=Quantity(
            value=OpticalPower(DBm(10.0 * math.log10(laser_mw)), PowerKind.AVERAGE),
            provenance=_prov(catalog, "guidedr.power_per_fiber"),
        ),
        laser_fiber_loss=q(DB(CHAIN_DB["laser_fiber_loss"])),
        coupling_loss=q(DB(CHAIN_DB["coupling_loss"])),
        split_n=q(n),
        excess_loss=q(DB(CHAIN_DB["excess_loss"])),
        modulator_il=q(DB(CHAIN_DB["modulator_il"])),
        output_coupler_loss=q(DB(CHAIN_DB["output_coupler_loss"])),
        extinction_ratio=q(DB(CHAIN_DB["extinction_ratio"])),
    )
    tx = base.tx.model_dump()
    tx.update(launch_oma_min=None, upstream=chain)
    return base.model_copy(update={"tx": Transmitter.model_validate(tx)})


def _guide(catalog: Catalog) -> tuple[Section, ...]:
    laser_mw = _value(catalog, "guidedr.power_per_fiber")
    items = []
    for n in (
        int(_value(catalog, "guidedr.lanes") / _value(catalog, "guidedr.fibers_max")),
        17,
        18,
    ):
        link = _chain_link(catalog, laser_mw, n)
        assert link.tx.upstream is not None
        oma, steps = derive_tp2(link.tx.upstream)
        report = evaluate(link)
        items.append(
            Item(
                label=f"N = {n}",
                value=f"P_TP2,avg {steps[-2].power_dbm:.4f} dBm, P_TP2,OMA "
                f"{oma.power_dbm.value:.4f} dBm, M {report.margin_db:+.4f} dB, {report.verdict}",
                unit="",
                source_class=INF,
            )
        )
    fanout = max_fanout(_chain_link(catalog, laser_mw, 4))
    items.append(Item(label="max fan-out", value=float(fanout), unit="", source_class=INF))
    return (
        Section(
            title="Guide DR: 200 mW per fiber through the §10 chain into the draft DR budget",
            items=tuple(items),
            note="4 lanes per fiber leaves about 6.4 dB unallocated: either the real chain loses "
            "about 6 dB more (H_chain_lossier) or the laser is provisioned for aging, "
            "temperature and TDECQ corners (H_laser_headroom). Model card §14.6.",
        ),
    )


def _pod(catalog: Catalog) -> tuple[Section, ...]:
    sections = []
    for h_id in ("H_pod_256", "H_pod_32"):
        bw = catalog.hypotheses[h_id].sets["pod.bw_per_xpu"]
        r = evaluate_pod(
            PodSpec(
                xpus=int(_value(catalog, "pod.size_gpus_cpx")),
                bw_per_xpu_tbps=bw,
                lane_gbps=_value(catalog, "l20.lane_rate"),
                ferrule_fibers=int(_value(catalog, "pod.ferrule_fibers")),
                claimed_fibers_before=_value(catalog, "pod.fibers_before_cpx"),
                claimed_fiber_saved_miles=(
                    _value(catalog, "pod.fiber_length_saved_cpx"),
                    _value(catalog, "pod.fiber_length_saved_hoti26"),
                ),
                claimed_connectors_saved=(
                    _value(catalog, "pod.connectors_saved_cpx"),
                    _value(catalog, "pod.connectors_saved_hoti26"),
                ),
            )
        )
        sections.append(
            Section(
                title=f"Pod at {bw:g} Tbps per XPU each way",
                hypothesis=h_id,
                items=(
                    Item(label="lanes per XPU", value=r.lanes_per_xpu, unit="", source_class=INF),
                    Item(label="duplex fibers", value=r.duplex_fibers, unit="", source_class=INF),
                    Item(label="BiDi fibers", value=r.bidi_fibers, unit="", source_class=INF),
                    Item(
                        label="gap to 'about 130,000'",
                        value=100.0 * (r.gap_to_claimed_fibers or 0),
                        unit="%",
                        source_class=INF,
                    ),
                    Item(
                        label="mean length of a removed fiber, 200 miles",
                        value=r.mean_length_m[0],
                        unit="m",
                        source_class=INF,
                    ),
                    Item(
                        label="mean length of a removed fiber, 150 miles",
                        value=r.mean_length_m[1],
                        unit="m",
                        source_class=INF,
                    ),
                    Item(
                        label="connectors per mating plane (16-fiber ferrules)",
                        value=r.connectors_per_mating_plane,
                        unit="",
                        source_class=INF,
                    ),
                    Item(
                        label="mated pairs per path, from '16,000' and '20,000'",
                        value=", ".join(f"{p:.2f}" for p in r.mated_pairs_per_path),
                        unit="",
                        source_class=INF,
                    ),
                ),
                note="Model card §14.8.",
            )
        )
    return tuple(sections)


def rack_spec(catalog: Catalog) -> RackSpec:
    """OICD-R64 from the catalog (model card §14.9)."""

    def qf(node_id: str) -> Quantity[float]:
        return Quantity(value=_value(catalog, node_id), provenance=_prov(catalog, node_id))

    def v(node_id: str) -> float:
        return _value(catalog, node_id)

    return RackSpec(
        frame_ou=Quantity(
            value=int(v("orv3.meta_capacity_openu")),
            provenance=_prov(catalog, "orv3.meta_capacity_openu"),
        ),
        ou_mm=qf("orv3.openu_pitch"),
        frame_mm=(
            qf("orv3.meta_frame_width"),
            qf("orv3.meta_frame_depth"),
            qf("orv3.meta_frame_height"),
        ),
        switch_trays=int(v("rack.switch_trays")),
        switch_tray_ou=int(v("rack.switch_tray_ou")),
        xpu_trays=int(v("rack.xpu_trays")),
        xpu_tray_ou={
            "H_2U": int(catalog.hypotheses["H_2U"].sets["rack.xpu_tray_ou"]),
            "H_1U": int(catalog.hypotheses["H_1U"].sets["rack.xpu_tray_ou"]),
        },
        power_shelves=int(v("rack.power_shelves")),
        power_shelf_ou=int(v("rack.power_shelf_ou")),
        xpus_per_tray=int(v("trays.xpu_accelerators")),
        lanes_per_xpu=int(v("rack.lanes_per_xpu")),
        switch_lanes=int(v("rack.switch_lanes")),
        lane_gbps=v("l20.lane_rate"),
        guide_dr_lanes=int(v("guidedr.lanes")),
        worst_path=(
            PathElement(name="XPU-side vClick", kind="vclick"),
            PathElement(
                name="tray fiber (XPU tray)", kind="fiber", length_m=qf("rack.tray_fiber_m")
            ),
            PathElement(
                name="PRIZM TMT blind mate",
                kind="connector",
                loss_db=qf("prizm.usconec_insertion_loss"),
            ),
            PathElement(name="rack fiber", kind="fiber", length_m=qf("rack.rack_fiber_m")),
            PathElement(
                name="switch-tray connector",
                kind="connector",
                loss_db=qf("rack.switch_connector_db"),
            ),
            PathElement(
                name="tray fiber (switch tray)", kind="fiber", length_m=qf("rack.tray_fiber_m")
            ),
            PathElement(name="switch-side vClick", kind="vclick"),
        ),
        vclick_loss_db=Quantity(
            value=v("vclick.il_reinsertion_max"),
            provenance=_prov(catalog, "vclick.il_reinsertion_max"),
        ),
        fiber_loss_db_per_km=qf("itut.g652d_atten_max"),
        budget=dr_budget_link(catalog, "OICD-R64 worst path"),
    )


def _rack(catalog: Catalog) -> tuple[Section, ...]:
    r = evaluate_rack(rack_spec(catalog))
    space = Section(
        title="Space in the Meta ORv3 frame",
        items=tuple(
            Item(
                label=f"{s.hypothesis}: OpenU used of {s.ou_available}",
                value=float(s.ou_used),
                unit="OU",
                source_class=INF,
                note="fits" if s.fits else "does not fit",
            )
            for s in r.space
        ),
        note="Model card §14.9.",
    )
    topology = Section(
        title="Single-tier topology and lasers",
        items=(
            Item(label="XPUs", value=float(r.xpus), unit="", source_class=SYN),
            Item(
                label="links (8 × 1024 switch lanes)",
                value=float(r.links),
                unit="",
                source_class=INF,
            ),
            Item(
                label="lanes per XPU per switch tray",
                value=r.lanes_per_xpu_per_switch_tray,
                unit="",
                source_class=INF,
            ),
            Item(label="BiDi fibers", value=float(r.bidi_fibers), unit="", source_class=INF),
            Item(label="duplex fibers", value=float(r.duplex_fibers), unit="", source_class=INF),
            Item(label="TX lanes", value=float(r.tx_lanes), unit="", source_class=INF),
            Item(label="Guide DR modules", value=r.guide_dr_total, unit="", source_class=INF),
            Item(
                label="Guide DR per XPU tray / per switch tray",
                value=f"{r.guide_dr_per_xpu_tray:g} / {r.guide_dr_per_switch_tray:g}",
                unit="",
                source_class=INF,
            ),
            Item(
                label="single-tier XPUs (switch lanes / lanes per XPU per plane)",
                value=r.single_tier_xpus,
                unit="",
                source_class=INF,
            ),
            Item(
                label="OCP vision flat domain",
                value=f"{r.ocp_vision_xpus[0]} to {r.ocp_vision_xpus[1]} XPUs",
                unit="",
                source_class=SourceClass.PROPOSED_STANDARD,
            ),
        ),
    )
    paths = tuple(
        Section(
            title=(
                f"Worst path, vClick {p.vclick_loss_db:g} dB in the channel"
                if p.vclick_loss_db is not None
                else "Worst path, vClick inside the module"
            ),
            hypothesis=p.hypothesis,
            items=(
                Item(label="fiber on the path", value=r.fiber_m, unit="m", source_class=SYN),
                Item(label="fiber loss", value=r.fiber_db, unit="dB", source_class=INF),
                Item(
                    label="channel insertion loss",
                    value=p.channel_il_db,
                    unit="dB",
                    source_class=INF,
                ),
                Item(
                    label="M_net on the draft DR budget",
                    value=p.report.margin_db,
                    unit="dB",
                    source_class=INF,
                ),
            ),
            verdict=p.report.verdict,
            note="The reference-plane definition, not the physics, decides this rack.",
        )
        for p in r.paths
    )
    yields = Section(
        title="Rack yield with independent links (statistical, assumption-dependent)",
        items=(
            *(
                Item(
                    label=f"link yield {y.link_yield:g}",
                    value=y.rack_yield,
                    unit="",
                    source_class=INF,
                )
                for y in r.yields
            ),
            Item(
                label=f"link yield for a {100 * r.rack_yield_target:g}% rack",
                value=r.link_yield_needed,
                unit="",
                source_class=INF,
            ),
            Item(label="one-sided z per link", value=r.z_needed, unit="σ", source_class=INF),
        ),
        note="Statistical design at rack scale returns to about 4.7σ per link.",
    )
    return (space, topology, *paths, yields)


EVALUATIONS: dict[str, Callable[[Catalog], tuple[Section, ...]]] = {
    "passage_l20": _l20,
    "passage_m1000": _m1000,
    "microring_ofc25": _ring_ofc25,
    "bidi_16lambda": _bidi16,
    "guide_family": _guide,
    "scaleup_pod": _pod,
    "reference_rack": _rack,
}


def physics_for(catalog: Catalog, product: str) -> ProductPhysics | None:
    """The product's physics evaluation, or None when it has none."""
    evaluation = EVALUATIONS.get(product)
    if evaluation is None:
        return None
    return ProductPhysics(product=product, sections=evaluation(catalog))
