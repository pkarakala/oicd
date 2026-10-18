"""BiDi reflection crosstalk (model card §12.4, bhatt2001_bidixtalk).

T = 10^(−IL/10), R = 10^(−(RL + I)/10), Π_xtalk = 10·log10(T/(T − R)), invalid if R ≥ T.

I = 0 is the source's single-wavelength formula. I > 0 (diplexer isolation of the receiver from
the local transmitter's wavelength) is OICD's two-wavelength extension, labeled INFERENCE.
"""

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from oicd.physics.mpi import mpi_penalty_db
from oicd.physics.ring import crosstalk_penalty
from oicd.provenance import Provenance, Quantity, SourceClass
from oicd.report import FeasibilityReport, evaluate
from oicd.schema import (
    FEC,
    ElectricalInterface,
    Link,
    LossElement,
    Penalty,
    Receiver,
    Transmitter,
)
from oicd.units import DB, DBm, OpticalPower, PowerKind

_FROZEN = ConfigDict(frozen=True, extra="forbid")

# Source rule (bhatt2001_bidixtalk): keep the return loss at least 5 dB above the channel IL.
RETURN_LOSS_RULE_MARGIN_DB = 5.0


class ReflectionCrosstalk(BaseModel):
    model_config = _FROZEN

    t_linear: float
    r_linear: float
    penalty_db: float
    rule_margin_db: float  # RL − (IL + 5 dB); ≥ 0 meets the source's thumb rule
    meets_return_loss_rule: bool
    source_class: SourceClass
    method: str


def _finite(value: float, name: str, *, minimum: float = 0.0) -> float:
    if not math.isfinite(value) or value < minimum:
        raise ValueError(f"{name} must be finite and >= {minimum}, got {value!r}")
    return float(value)


def reflection_crosstalk_db(
    il_db: float, rl_db: float, isolation_db: float = 0.0
) -> ReflectionCrosstalk:
    """Crosstalk penalty from the local transmitter's reflection reaching the local receiver."""
    il = _finite(il_db, "il_db")
    rl = _finite(rl_db, "rl_db")
    isolation = _finite(isolation_db, "isolation_db")
    t = 10.0 ** (-il / 10.0)
    r = 10.0 ** (-(rl + isolation) / 10.0)
    if r >= t:
        raise ValueError(
            f"reflection ({rl + isolation} dB below launch) is not below the signal "
            f"({il} dB below launch): the crosstalk penalty is unbounded"
        )
    margin = rl - (il + RETURN_LOSS_RULE_MARGIN_DB)
    extension = isolation > 0.0
    return ReflectionCrosstalk(
        t_linear=t,
        r_linear=r,
        penalty_db=10.0 * math.log10(t / (t - r)),
        rule_margin_db=margin,
        meets_return_loss_rule=margin >= 0.0,
        source_class=SourceClass.INFERENCE if extension else SourceClass.PROPOSED_STANDARD,
        method=(
            "bhatt2001_bidixtalk with diplexer isolation added to the return loss (INFERENCE)"
            if extension
            else "bhatt2001_bidixtalk single-wavelength formula"
        ),
    )


# ---- BiDi link model (model card §13.7) ----------------------------------------------------
#
# Each direction is a §3 link: TX OMA at the engine output, the TX-end diplexer, the passive
# channel (fiber and connectors), the RX-end diplexer, then the RX sensitivity. Named penalties:
# reflection crosstalk of the local transmitter (§12.4, from the channel IL, the return loss and
# the diplexer isolation), MPI (§12.3) and co-directional WDM crosstalk (§13.2). Each direction is
# evaluated by oicd.report.evaluate; the link is NOT_EXCLUDED iff both directions are.

WHAT_IF = Provenance(
    source_class=SourceClass.SYNTHETIC,
    rationale="Entered as a what-if input of the BiDi link model (not from a source).",
)
G652_MAX_DB_PER_KM = 0.4  # ITU-T G.652.D maximum attenuation, 1310 to 1625 nm (itut_g652_2024)
G652 = Provenance(
    source_class=SourceClass.PUBLISHED_SPEC,
    citation_key="itut_g652_2024",
    rationale="ITU-T G.652 (08/2024): maximum attenuation 0.40 dB/km from 1310 to 1625 nm.",
)


def _quantity(value: object) -> object:
    """Accept a bare number as a what-if input (SYNTHETIC), or a {value, provenance} quantity."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return {"value": float(value), "provenance": WHAT_IF.model_dump()}
    return value


class BidiDirection(BaseModel):
    """One direction of a BiDi link, as the engine at each end specifies it."""

    model_config = _FROZEN

    name: str
    modulation: Literal["NRZ", "PAM4"]
    symbol_rate_gbd: float = Field(gt=0, allow_inf_nan=False)
    fec: FEC = FEC.RS_544_514
    tx_oma_dbm: Quantity[float]  # at the TX engine output, before its diplexer
    tx_center_nm: Quantity[float]
    tx_tolerance_nm: Quantity[float]
    rx_passband_min_nm: Quantity[float]
    rx_passband_max_nm: Quantity[float]
    rx_sensitivity_dbm: Quantity[float]  # OMA at the RX engine input, after its diplexer
    wdm_leakage: Quantity[float] | None = None  # X of §13.2 for this direction's worst ring
    extra_penalties_db: dict[str, Quantity[float]] = {}

    _wrap = field_validator(
        "tx_oma_dbm",
        "tx_center_nm",
        "tx_tolerance_nm",
        "rx_passband_min_nm",
        "rx_passband_max_nm",
        "rx_sensitivity_dbm",
        "wdm_leakage",
        mode="before",
    )(_quantity)

    @field_validator("extra_penalties_db", mode="before")
    @classmethod
    def _wrap_extra(cls, value: object) -> object:
        if isinstance(value, dict):
            return {k: _quantity(v) for k, v in value.items()}
        return value


class MpiInputs(BaseModel):
    model_config = _FROZEN

    m_levels: int
    er_db: float
    rt_db: float
    rr_db: float
    rc_db: float
    n_connectors: int
    provenance: Provenance = WHAT_IF


class BidiLinkRequest(BaseModel):
    model_config = _FROZEN

    name: str = "BiDi link"
    a_to_b: BidiDirection
    b_to_a: BidiDirection
    diplexer_il_db: Quantity[float]  # each end
    diplexer_isolation_db: Quantity[float]  # RX path isolation from the local TX wavelength
    fiber_length_km: Quantity[float]
    fiber_loss_db_per_km: Quantity[float] = Quantity(value=G652_MAX_DB_PER_KM, provenance=G652)
    connector_losses_db: tuple[Quantity[float], ...] = ()
    return_loss_db: Quantity[float]  # at each fiber interface (ORL seen by the transmitter)
    mpi: MpiInputs | None = None
    reserve_db: Quantity[float] = Quantity(value=0.0, provenance=WHAT_IF)

    _wrap = field_validator(
        "diplexer_il_db",
        "diplexer_isolation_db",
        "fiber_length_km",
        "fiber_loss_db_per_km",
        "return_loss_db",
        "reserve_db",
        mode="before",
    )(_quantity)

    @field_validator("connector_losses_db", mode="before")
    @classmethod
    def _wrap_connectors(cls, value: object) -> object:
        if isinstance(value, (list, tuple)):
            return tuple(_quantity(v) for v in value)
        return value


class BidiDirectionResult(BaseModel):
    model_config = _FROZEN

    name: str
    report: FeasibilityReport
    channel_il_db: float  # TP2 to TP3 passive channel, for the reflection crosstalk
    reflection: ReflectionCrosstalk
    mpi_db: float | None
    wdm_crosstalk_db: float | None
    min_tx_oma_dbm: float  # the TX OMA at which this direction's margin is 0 dB


class BidiLinkResult(BaseModel):
    model_config = _FROZEN

    name: str
    verdict: Literal["NOT_EXCLUDED", "EXCLUDED"]
    margin_db: float  # the smaller of the two directions
    deciding_direction: str
    directions: tuple[BidiDirectionResult, ...]


def _db_q(q: Quantity[float]) -> Quantity[DB]:
    return Quantity(value=DB(q.value), provenance=q.provenance)


def _penalty(name: str, value_db: float, rationale: str) -> Penalty:
    return Penalty(
        name=name,
        value=Quantity(
            value=DB(value_db),
            provenance=Provenance(source_class=SourceClass.INFERENCE, rationale=rationale),
        ),
    )


def _direction(request: BidiLinkRequest, d: BidiDirection) -> BidiDirectionResult:
    fiber_db = request.fiber_length_km.value * request.fiber_loss_db_per_km.value
    fiber = LossElement(
        name=f"fiber {request.fiber_length_km.value:g} km",
        loss_max=Quantity(
            value=DB(fiber_db),
            provenance=Provenance(
                source_class=SourceClass.INFERENCE,
                rationale=(
                    f"{request.fiber_length_km.value:g} km × "
                    f"{request.fiber_loss_db_per_km.value:g} dB/km (length "
                    f"{request.fiber_length_km.provenance.source_class.value}, attenuation "
                    f"{request.fiber_loss_db_per_km.provenance.source_class.value})."
                ),
            ),
        ),
    )
    connectors = tuple(
        LossElement(name=f"connector {i + 1}", loss_max=_db_q(c))
        for i, c in enumerate(request.connector_losses_db)
    )
    channel_il = fiber_db + sum(c.value for c in request.connector_losses_db)
    reflection = reflection_crosstalk_db(
        channel_il, request.return_loss_db.value, request.diplexer_isolation_db.value
    )
    penalties = [
        _penalty(
            "reflection crosstalk",
            reflection.penalty_db,
            f"model card §12.4 at channel IL {channel_il:g} dB, RL "
            f"{request.return_loss_db.value:g} dB, isolation "
            f"{request.diplexer_isolation_db.value:g} dB",
        )
    ]
    mpi_db = None
    if request.mpi is not None:
        m = request.mpi
        mpi_db = mpi_penalty_db(
            m.m_levels, m.er_db, m.rt_db, m.rr_db, m.rc_db, m.n_connectors
        ).penalty_db
        penalties.append(
            _penalty("MPI", mpi_db, "model card §12.3 worst-case bound (bhatt2016_mpi)")
        )
    wdm_db = None
    if d.wdm_leakage is not None and d.wdm_leakage.value > 0.0:
        wdm_db = crosstalk_penalty(d.wdm_leakage.value, d.modulation).penalty_db
        penalties.append(
            _penalty("WDM crosstalk", wdm_db, f"model card §13.2 at X = {d.wdm_leakage.value:g}")
        )
    penalties += [Penalty(name=n, value=_db_q(q)) for n, q in sorted(d.extra_penalties_db.items())]
    electrical = ElectricalInterface(
        modulation=d.modulation,
        symbol_rate_gbd=d.symbol_rate_gbd,
        lanes=1,
        fec=d.fec,
        provenance=WHAT_IF,
    )
    link = Link(
        name=f"{request.name}: {d.name}",
        tx=Transmitter(
            name=f"{d.name} TX",
            electrical=electrical,
            center_wavelength_nm=d.tx_center_nm,
            wavelength_tolerance_nm=d.tx_tolerance_nm,
            launch_oma_min=Quantity(
                value=OpticalPower(DBm(d.tx_oma_dbm.value), PowerKind.OMA),
                provenance=d.tx_oma_dbm.provenance,
            ),
        ),
        rx=Receiver(
            name=f"{d.name} RX",
            electrical=electrical,
            passband_min_nm=d.rx_passband_min_nm,
            passband_max_nm=d.rx_passband_max_nm,
            sensitivity_oma_max=Quantity(
                value=OpticalPower(DBm(d.rx_sensitivity_dbm.value), PowerKind.OMA),
                provenance=d.rx_sensitivity_dbm.provenance,
            ),
        ),
        channel=(
            LossElement(name="TX-end diplexer", loss_max=_db_q(request.diplexer_il_db)),
            fiber,
            *connectors,
            LossElement(name="RX-end diplexer", loss_max=_db_q(request.diplexer_il_db)),
        ),
        penalties=tuple(penalties),
        reserve=_db_q(request.reserve_db),
    )
    report = evaluate(link)
    total_loss = float(report.results[2].evidence["total_loss_db"])
    return BidiDirectionResult(
        name=d.name,
        report=report,
        channel_il_db=channel_il,
        reflection=reflection,
        mpi_db=mpi_db,
        wdm_crosstalk_db=wdm_db,
        min_tx_oma_dbm=report.threshold_dbm + total_loss,
    )


def evaluate_bidi_link(request: BidiLinkRequest) -> BidiLinkResult:
    """Both directions of a BiDi link (model card §13.7)."""
    results = (_direction(request, request.a_to_b), _direction(request, request.b_to_a))
    deciding = min(results, key=lambda r: (r.report.verdict != "EXCLUDED", r.report.margin_db))
    return BidiLinkResult(
        name=request.name,
        verdict="EXCLUDED"
        if any(r.report.verdict == "EXCLUDED" for r in results)
        else "NOT_EXCLUDED",
        margin_db=min(r.report.margin_db for r in results),
        deciding_direction=deciding.name,
        directions=results,
    )
