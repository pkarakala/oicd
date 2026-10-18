"""Model card §10: upstream chain, TP2 derived. Expected values are copied from the card."""

import pytest

from oicd.paths import set_input
from oicd.provenance import SourceClass
from oicd.report import evaluate
from oicd.schema import Transmitter
from oicd.units import PowerKind, UnitMismatchError
from oicd.upstream import derive_tp2, max_fanout, split_loss_db

from .conftest import build_chain, with_chain

TOL = 1e-4  # §10 hand-case tolerance

# §10 table: N -> (P_TP2,avg dBm, P_TP2,OMA dBm, M_net dB, verdict).
CARD_TABLE = {
    16: (0.4588, -0.1911, 0.3081, "NOT_EXCLUDED"),
    17: (0.1955, -0.4544, 0.0448, "NOT_EXCLUDED"),
    18: (-0.0527, -0.7026, -0.2034, "EXCLUDED"),
}


@pytest.mark.parametrize("n", sorted(CARD_TABLE))
def test_hand_case_table(worked_example, n):
    p_avg, p_oma, margin, verdict = CARD_TABLE[n]
    oma, steps = derive_tp2(build_chain(split_n=n))
    assert oma.kind is PowerKind.OMA
    assert steps[-2].power_dbm == pytest.approx(p_avg, abs=TOL)
    assert oma.power_dbm.value == pytest.approx(p_oma, abs=TOL)
    report = evaluate(with_chain(worked_example, build_chain(split_n=n)))
    assert report.margin_db == pytest.approx(margin, abs=TOL)
    assert report.verdict == verdict
    assert report.upstream is not None
    assert report.upstream.p_tp2_avg_dbm == pytest.approx(p_avg, abs=TOL)
    assert report.upstream.p_tp2_oma_dbm == pytest.approx(p_oma, abs=TOL)


def test_max_fanout_is_17(worked_example):
    # §10: max fan-out 17.
    link = with_chain(worked_example, build_chain(split_n=16))
    assert max_fanout(link) == 17
    assert evaluate(link).upstream.max_fanout == 17


def test_trace_is_itemized_and_tp2_matches(worked_example):
    report = evaluate(with_chain(worked_example, build_chain(split_n=16)))
    section = report.upstream
    assert [s.input_path for s in section.steps] == [
        "tx.upstream.laser_power_avg",
        "tx.upstream.laser_fiber_loss",
        "tx.upstream.coupling_loss",
        "tx.upstream.split_n",
        "tx.upstream.excess_loss",
        "tx.upstream.modulator_il",
        "tx.upstream.output_coupler_loss",
        "tx.upstream.extinction_ratio",
    ]
    assert [s.kind for s in section.steps] == ["average"] * 7 + ["oma"]
    assert section.steps[3].loss_db == pytest.approx(12.0412, abs=TOL)  # 10·log10(16)
    assert report.power_trace[0].power_dbm == section.p_tp2_oma_dbm
    assert section.tp2_source_class is SourceClass.INFERENCE
    paths = {r.path for r in report.inputs}
    assert "tx.launch_oma_min" not in paths
    assert {s.input_path for s in section.steps} <= paths
    assert report.results[2].evidence["tp2_source"] == "upstream chain"


def test_each_doubling_costs_3_0103_db(worked_example):
    # §10 why-line: each doubling of N costs 10·log10(2) = 3.0103 dB.
    m8 = evaluate(with_chain(worked_example, build_chain(split_n=8))).margin_db
    m16 = evaluate(with_chain(worked_example, build_chain(split_n=16))).margin_db
    assert m8 - m16 == pytest.approx(3.0103, abs=TOL)
    assert split_loss_db(2).value == pytest.approx(3.0103, abs=TOL)


def test_fanout_zero_when_one_output_already_fails(worked_example):
    link = with_chain(worked_example, build_chain(laser_dbm=5.0))
    assert evaluate(link).verdict == "EXCLUDED"
    assert max_fanout(link) == 0


def test_fanout_zero_when_wavelength_fails(worked_example):
    link = set_input(with_chain(worked_example, build_chain()), "tx.center_wavelength_nm", 1330.0)
    assert max_fanout(link) == 0


def test_exactly_one_tp2_source(worked_example):
    tx = worked_example.tx.model_dump()
    with pytest.raises(ValueError, match="exactly one"):
        Transmitter.model_validate({**tx, "upstream": build_chain()})
    with pytest.raises(ValueError, match="exactly one"):
        Transmitter.model_validate({**tx, "launch_oma_min": None})


@pytest.mark.parametrize(
    "bad",
    [{"split_n": 0}, {"modulator_db": -0.1}, {"er_db": 0.0}, {"coupling_db": float("nan")}],
    ids=lambda bad: ",".join(bad),
)
def test_invalid_chain_physics(bad):
    with pytest.raises(ValueError):
        build_chain(**bad)


def test_laser_power_must_be_average():
    with pytest.raises(UnitMismatchError):
        build_chain(laser_kind=PowerKind.OMA)
