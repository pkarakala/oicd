"""Model card §12: draft IEEE 802.3dj DR budget, Table 180-12, MPI bound, reflection crosstalk.

Expected values are copied from the card (and through it from the cited sources).
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from oicd.physics.bidi import reflection_crosstalk_db
from oicd.physics.mpi import mpi_penalty_db
from oicd.profiles import load_link, profile_path
from oicd.provenance import SourceClass
from oicd.report import evaluate
from oicd.standards import max_channel_il


@pytest.fixture(scope="module")
def dr_report():
    return evaluate(load_link(profile_path("ieee_dr_200g")))


def test_dr_budget_closes_at_zero(dr_report):
    # §12.1: M_net = 0 on paper; float -4.44e-16, so assert NOT_EXCLUDED and |M| < 1e-9.
    assert dr_report.verdict == "NOT_EXCLUDED"
    assert abs(dr_report.margin_db) < 1e-9
    assert all(r.status.value == "pass" for r in dr_report.results)


def test_dr_budget_terms(dr_report):
    # §12.1: P_TP2 = 2.4 dBm, S_RX = -4.3 dBm, channel 3.0 dB, penalties 3.4 + 0.1 + 0.2 = 3.7.
    budget = dr_report.results[2].evidence
    assert dr_report.power_trace[0].power_dbm == 2.4
    assert budget["sensitivity_dbm"] == -4.3
    assert budget["total_loss_db"] == 3.0
    assert budget["penalties_db"] == pytest.approx(3.7, abs=1e-12)
    assert budget["penalty_names"] == "TDECQ, MPI, DGD"
    # Power budget 6.7 dB = P_TP2 - S_RX; allocation for penalties 3.7 dB = 6.7 - 3.0.
    assert 2.4 - (-4.3) == pytest.approx(6.7, abs=1e-12)
    wavelength = dr_report.results[1].evidence
    assert abs(wavelength["lower_clearance_nm"]) < 1e-9
    assert abs(wavelength["upper_clearance_nm"]) < 1e-9


def test_dr_profile_provenance(dr_report):
    # §12: every draft value is PROPOSED_STANDARD with a citation; the reserve is SYNTHETIC.
    for record in dr_report.inputs:
        if record.path == "reserve":
            assert record.source_class is SourceClass.SYNTHETIC
        else:
            assert record.source_class is SourceClass.PROPOSED_STANDARD
            assert record.citation_key in {"welch2023_3dj_baseline", "johnson2025_3dj_mpidgd"}
            assert "not an approved standard" in record.rationale


@pytest.mark.parametrize(
    "counts, expected",
    [((0, 0), 3.0), ((0, 6), 2.9), ((2, 3), 2.8), ((4, 4), 2.5), ((5, 0), 2.5)],
)
def test_table_180_12(counts, expected):
    il = max_channel_il(*counts)
    assert il is not None
    assert il.value.value == expected
    assert il.provenance.source_class is SourceClass.PROPOSED_STANDARD


@pytest.mark.parametrize("counts", [(4, 8), (6, 0), (7, 0), (0, 9)])
def test_table_180_12_not_supported(counts):
    assert max_channel_il(*counts) is None


@pytest.mark.parametrize("counts", [(-1, 0), (0, -1), (1.5, 0), (True, 0)])
def test_table_180_12_invalid_counts(counts):
    with pytest.raises(ValueError):
        max_channel_il(*counts)


@given(row=st.integers(min_value=0, max_value=5), col=st.integers(min_value=0, max_value=7))
def test_table_180_12_never_rises_with_more_reflectances(row, col):
    here = max_channel_il(row, col)
    for more in (max_channel_il(row + 1, col), max_channel_il(row, col + 1)):
        if here is not None and more is not None:
            assert more.value.value <= here.value.value


@pytest.mark.parametrize("n, expected", [(2, 0.8142), (4, 1.4378), (6, 2.3137)])
def test_mpi_published_example(n, expected):
    # §12.3: PAM4, ER 6 dB, Rt -20, Rr -26, Rc -35 dB -> 0.8142, 1.4378, 2.3137 dB.
    result = mpi_penalty_db(4, 6.0, -20.0, -26.0, -35.0, n)
    assert result.penalty_db == pytest.approx(expected, abs=5e-5)
    assert "worst-case bound" in result.method


def test_mpi_rises_with_connectors():
    penalties = [mpi_penalty_db(4, 6.0, -20.0, -26.0, -35.0, n).penalty_db for n in range(7)]
    assert penalties == sorted(penalties)


@pytest.mark.parametrize(
    "args",
    [
        (4, 6.0, -10.0, -10.0, -10.0, 6),  # x >= 1: the bound diverges
        (1, 6.0, -20.0, -26.0, -35.0, 2),  # m < 2
        (4, 0.0, -20.0, -26.0, -35.0, 2),  # ER <= 0 dB
        (4, 6.0, 3.0, -26.0, -35.0, 2),  # reflectance > 0 dB
        (4, 6.0, -20.0, -26.0, -35.0, -1),  # negative connector count
    ],
)
def test_mpi_invalid_input(args):
    with pytest.raises(ValueError):
        mpi_penalty_db(*args)


def test_reflection_crosstalk_published_example():
    # §12.4: IL 7 dB, RL 12 dB -> 1.6509 dB (source ≈ 1.65), the single-wavelength formula.
    result = reflection_crosstalk_db(7.0, 12.0)
    assert result.penalty_db == pytest.approx(1.6509, abs=5e-5)
    assert result.source_class is SourceClass.PROPOSED_STANDARD
    assert result.meets_return_loss_rule is True  # 12 >= 7 + 5


@pytest.mark.parametrize("isolation, expected", [(0.0, 0.2514), (25.0, 0.000772)])
def test_reflection_crosstalk_two_wavelength_extension(isolation, expected):
    # §12.4 extension (INFERENCE): IL 3, RL 15.5 dB; I 0 -> 0.2514 dB; I 25 dB -> 0.000772 dB.
    result = reflection_crosstalk_db(3.0, 15.5, isolation)
    assert result.penalty_db == pytest.approx(expected, rel=1e-3)
    expected_class = SourceClass.INFERENCE if isolation > 0 else SourceClass.PROPOSED_STANDARD
    assert result.source_class is expected_class


def test_return_loss_rule():
    assert reflection_crosstalk_db(3.0, 8.0).meets_return_loss_rule is True
    assert reflection_crosstalk_db(3.0, 7.9).meets_return_loss_rule is False


@given(
    il=st.floats(min_value=0.0, max_value=10.0),
    rl=st.floats(min_value=11.0, max_value=40.0),
    extra=st.floats(min_value=0.01, max_value=10.0),
)
def test_more_return_loss_means_less_crosstalk(il, rl, extra):
    assert (
        reflection_crosstalk_db(il, rl + extra).penalty_db
        < reflection_crosstalk_db(il, rl).penalty_db
    )


def test_reflection_stronger_than_signal_is_invalid():
    with pytest.raises(ValueError):
        reflection_crosstalk_db(12.0, 7.0)
