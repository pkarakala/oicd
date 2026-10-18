"""Shared fixtures: the model card §4 worked example and a builder for §5 variants.

All values are SYNTHETIC. Fixtures are session-scoped because the models are immutable
(and so hypothesis can use them).
"""

import pytest

from oicd.provenance import Provenance, Quantity, SourceClass
from oicd.schema import (
    FEC,
    ElectricalInterface,
    Link,
    LossDistribution,
    LossElement,
    Penalty,
    Receiver,
    Transmitter,
    UpstreamChain,
)
from oicd.units import DB, DBm, OpticalPower, PowerKind

WORKED_EXAMPLE = Provenance(
    source_class=SourceClass.SYNTHETIC,
    rationale="Model card §4 worked example input (synthetic, not a datasheet value).",
)
CARD_T09 = Provenance(
    source_class=SourceClass.SYNTHETIC,
    rationale="§4 gives no wavelengths; model card T09 values used (synthetic).",
)
REPRESENTATIVE_200G = Provenance(
    source_class=SourceClass.SYNTHETIC,
    rationale="§4 gives no electrical values; model card T11 TX lane (106.25 GBd PAM4) used, "
    "FEC assumed RS(544,514); IEEE 802.3 clause not yet cited.",
)

# Model card §4 channel, TP2 to TP3, in the §2 order (fiber as two 1 m segments).
WORKED_EXAMPLE_CHANNEL_DB = (
    ("TX FAU mating", 1.5),
    ("SMF 1 m (TX side)", 0.0004),
    ("patch connector", 1.0),
    ("SMF 1 m (RX side)", 0.0004),
    ("RX FAU mating", 1.5),
)


def _q(value: object, provenance: Provenance = WORKED_EXAMPLE) -> Quantity:
    return Quantity(value=value, provenance=provenance)


def build_link(
    *,
    channel_db: tuple[tuple[str, float], ...] = (("lumped channel", 4.0),),
    penalties_db: tuple[tuple[str, float], ...] = (),
    reserve_db: float = 1.5,
    launch_dbm: float = 0.0,
    launch_kind: PowerKind = PowerKind.OMA,
    sensitivity_dbm: float = -6.0,
    sensitivity_kind: PowerKind = PowerKind.OMA,
    tx_center_nm: float = 1310.0,
    tx_tolerance_nm: float = 2.0,
    rx_min_nm: float = 1300.0,
    rx_max_nm: float = 1320.0,
    tx_symbol_rate_gbd: float = 106.25,
    rx_symbol_rate_gbd: float = 106.25,
    modulation: str = "PAM4",
    lanes: int = 1,
    tx_fec: str = FEC.RS_544_514,
    rx_fec: str = FEC.RS_544_514,
) -> Link:
    """Build a validated Link. Defaults are model card §5 T01 (P_TP2 0 dBm, loss 4.0 dB,
    S_RX -6 dBm, Π 0, R 1.5 dB) with T09 wavelengths."""

    def electrical(symbol_rate_gbd: float, fec: str) -> ElectricalInterface:
        return ElectricalInterface(
            modulation=modulation,
            symbol_rate_gbd=symbol_rate_gbd,
            lanes=lanes,
            fec=fec,
            provenance=REPRESENTATIVE_200G,
        )

    tx = Transmitter(
        name="synthetic TX",
        electrical=electrical(tx_symbol_rate_gbd, tx_fec),
        center_wavelength_nm=_q(tx_center_nm, CARD_T09),
        wavelength_tolerance_nm=_q(tx_tolerance_nm, CARD_T09),
        launch_oma_min=_q(OpticalPower(DBm(launch_dbm), launch_kind)),
    )
    rx = Receiver(
        name="synthetic RX",
        electrical=electrical(rx_symbol_rate_gbd, rx_fec),
        passband_min_nm=_q(rx_min_nm, CARD_T09),
        passband_max_nm=_q(rx_max_nm, CARD_T09),
        sensitivity_oma_max=_q(OpticalPower(DBm(sensitivity_dbm), sensitivity_kind)),
    )
    return Link(
        tx=tx,
        rx=rx,
        channel=tuple(LossElement(name=n, loss_max=_q(DB(v))) for n, v in channel_db),
        penalties=tuple(Penalty(name=n, value=_q(DB(v))) for n, v in penalties_db),
        reserve=_q(DB(reserve_db)),
    )


@pytest.fixture(scope="session")
def worked_example() -> Link:
    return build_link(channel_db=WORKED_EXAMPLE_CHANNEL_DB)


@pytest.fixture(scope="session")
def make_link():
    return build_link


UPSTREAM_CARD = Provenance(
    source_class=SourceClass.SYNTHETIC,
    rationale="Model card §10 hand-case upstream input (synthetic, not a datasheet value).",
)
SIGMA_CARD = Provenance(
    source_class=SourceClass.SYNTHETIC,
    rationale="Model card §11 hand case: sigma 0.2 dB per mating (synthetic assumption).",
)


def build_chain(
    *,
    split_n: int = 16,
    laser_dbm: float = 20.0,
    laser_fiber_db: float = 0.5,
    coupling_db: float = 1.5,
    excess_db: float = 0.0,
    modulator_db: float = 4.0,
    coupler_db: float = 1.5,
    er_db: float = 4.0,
    laser_kind: PowerKind = PowerKind.AVERAGE,
) -> UpstreamChain:
    """Model card §10 hand-case chain (all SYNTHETIC)."""

    def q(value: object) -> Quantity:
        return Quantity(value=value, provenance=UPSTREAM_CARD)

    return UpstreamChain(
        laser_power_avg=q(OpticalPower(DBm(laser_dbm), laser_kind)),
        laser_fiber_loss=q(DB(laser_fiber_db)),
        coupling_loss=q(DB(coupling_db)),
        split_n=q(split_n),
        excess_loss=q(DB(excess_db)),
        modulator_il=q(DB(modulator_db)),
        output_coupler_loss=q(DB(coupler_db)),
        extinction_ratio=q(DB(er_db)),
    )


def with_chain(link: Link, chain: UpstreamChain) -> Link:
    """The link with its fixed TP2 replaced by an upstream chain."""
    tx = link.tx.model_dump()
    tx.update(launch_oma_min=None, upstream=chain)
    return link.model_copy(update={"tx": Transmitter.model_validate(tx)})


def with_sigma(link: Link, indices: tuple[int, ...], sigma_db: float) -> Link:
    """The link with N(loss_max, sigma²) distributions on the given channel elements (§11)."""
    channel = tuple(
        e.model_copy(
            update={
                "loss_distribution": LossDistribution(
                    mean=Quantity(value=e.loss_max.value, provenance=SIGMA_CARD),
                    sigma=Quantity(value=DB(sigma_db), provenance=SIGMA_CARD),
                )
            }
        )
        if i in indices
        else e
        for i, e in enumerate(link.channel)
    )
    return link.model_copy(update={"channel": channel})


@pytest.fixture(scope="session")
def make_chain():
    return build_chain
