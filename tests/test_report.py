"""Report, profiles and model card §5 cases T13 to T15.

Expected values come from docs/model_card.md (§4 worked example, §5 table).
"""

import json

import pytest
from hypothesis import given
from hypothesis import strategies as st

from oicd.checks import Status
from oicd.profiles import PROFILES_DIR, load_link, profile_path
from oicd.provenance import SourceClass
from oicd.registry import EPSILON_DB, ConstraintId
from oicd.report import FeasibilityReport, evaluate
from oicd.schema import Link

WORKED_EXAMPLE_JSON = PROFILES_DIR / "worked_example.json"


@pytest.fixture(scope="module")
def profile_link() -> Link:
    return load_link(WORKED_EXAMPLE_JSON)


@pytest.fixture(scope="module")
def profile_report(profile_link) -> FeasibilityReport:
    return evaluate(profile_link)


def test_T13_every_input_lists_its_source_class(profile_report):
    # T13: every input in the report lists its SourceClass (all SYNTHETIC here).
    paths = {record.path for record in profile_report.inputs}
    expected = {
        *(
            f"{side}.electrical.{f}"
            for side in ("tx", "rx")
            for f in ("modulation", "symbol_rate_gbd", "lanes", "fec")
        ),
        "tx.center_wavelength_nm",
        "tx.wavelength_tolerance_nm",
        "tx.launch_oma_min",
        "rx.passband_min_nm",
        "rx.passband_max_nm",
        "rx.sensitivity_oma_max",
        *(f"channel[{i}].loss_max" for i in range(5)),
        "reserve",
    }
    assert paths == expected
    for record in profile_report.inputs:
        assert record.source_class is SourceClass.SYNTHETIC
        assert record.citation_key is None
        assert record.rationale.strip()


def test_T14_two_runs_give_identical_json(make_link, profile_link):
    # T14: run T01 twice -> identical reports, field for field (and byte for byte as JSON).
    t01 = make_link()
    assert evaluate(t01) == evaluate(t01)
    assert evaluate(t01).to_json() == evaluate(t01).to_json()
    assert evaluate(profile_link).to_json() == evaluate(load_link(WORKED_EXAMPLE_JSON)).to_json()


def test_to_json_sorts_keys(profile_report):
    text = profile_report.to_json()
    assert text == json.dumps(
        json.loads(text), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def test_T15_not_evaluated_list(make_link):
    # T15: any link -> lists BER, TDECQ, dispersion, reflections/MPI, thermal, reliability.
    report = evaluate(make_link())
    assert [r.constraint for r in report.not_evaluated] == [
        ConstraintId.BER,
        ConstraintId.TDECQ,
        ConstraintId.DISPERSION,
        ConstraintId.REFLECTIONS_MPI,
        ConstraintId.THERMAL,
        ConstraintId.RELIABILITY,
    ]
    for result in report.not_evaluated:
        assert result.status is Status.NOT_EVALUATED
        assert result.message.strip() and "\n" not in result.message


def test_worked_example_report(profile_report):
    # §4: M_net = +0.4992 dB, PASS; threshold = S_RX + Π + R = -6 + 0 + 1.5 = -4.5 dBm.
    assert profile_report.verdict == "NOT_EXCLUDED"
    assert profile_report.margin_db == pytest.approx(0.4992, abs=1e-12)
    assert profile_report.threshold_dbm == -4.5
    assert [r.constraint for r in profile_report.results] == [
        ConstraintId.ELECTRICAL_MATCH,
        ConstraintId.WAVELENGTH_CONTAINMENT,
        ConstraintId.OPTICAL_POWER_BUDGET,
    ]
    assert all(r.status is Status.PASS for r in profile_report.results)


def test_power_trace_worked_example(profile_report):
    # §4: P_TP2 = 0 dBm OMA; after 1.5, 0.0004, 1.0, 0.0004, 1.5 dB the TP3 OMA is -4.0008 dBm.
    trace = profile_report.power_trace
    assert [p.name for p in trace] == [
        "TP2",
        "TX FAU mating",
        "SMF 1 m (TX side)",
        "patch connector",
        "SMF 1 m (RX side)",
        "RX FAU mating",
        "TP3",
    ]
    expected_dbm = [0.0, -1.5, -1.5004, -2.5004, -2.5008, -4.0008, -4.0008]
    for point, dbm in zip(trace, expected_dbm, strict=True):
        assert point.power_dbm == pytest.approx(dbm, abs=1e-12)
    assert trace[-1].power_dbm == pytest.approx(-4.0008, abs=1e-12)
    budget = profile_report.results[2]
    assert trace[-1].power_dbm == budget.evidence["p_tp3_dbm"]
    # Headroom above threshold (-4.5 dBm) at TP3 equals the margin, 0.4992 dB.
    assert trace[-1].headroom_db == pytest.approx(0.4992, abs=1e-12)
    assert [p.channel_index for p in trace] == [None, 0, 1, 2, 3, 4, None]
    assert sum(p.loss_fraction for p in trace if p.loss_fraction is not None) == pytest.approx(1.0)
    # §3: power_mw = 10^(P/10); TP2 1.0 mW, TP3 0.398034 mW
    assert trace[0].power_mw == pytest.approx(1.0, abs=1e-12)
    assert trace[-1].power_mw == pytest.approx(0.398034, abs=1e-6)
    assert trace[0].relative_power == 1.0
    assert trace[-1].relative_power == pytest.approx(0.398034, abs=1e-6)


def test_report_and_evidence_name_the_penalty(make_link):
    # T06 (updated card): report and check evidence name the penalty.
    report = evaluate(make_link(channel_db=(("channel", 4.0),), penalties_db=(("TDECQ", 1.0),)))
    assert report.verdict == "EXCLUDED"
    assert report.margin_db == -0.5
    assert report.results[2].evidence["penalty_names"] == "TDECQ"
    penalty_inputs = [r for r in report.inputs if r.path.startswith("penalties[")]
    assert [(r.path, r.name, r.value) for r in penalty_inputs] == [
        ("penalties[0].value", "TDECQ", 1.0)
    ]


def test_profile_json_round_trip(profile_link):
    text = profile_link.model_dump_json()
    assert Link.model_validate_json(text) == profile_link
    assert evaluate(Link.model_validate_json(text)).to_json() == evaluate(profile_link).to_json()


def test_profile_rejects_invalid_physics(profile_link):
    data = json.loads(profile_link.model_dump_json())
    data["channel"][0]["loss_max"]["value"]["value"] = -1.0
    with pytest.raises(ValueError):
        Link.model_validate(data)


def test_profile_path_rejects_unknown_and_traversal():
    assert profile_path("worked_example") == WORKED_EXAMPLE_JSON
    for bad in ("no_such_profile", "../pyproject", "worked_example.json", ""):
        with pytest.raises(FileNotFoundError):
            profile_path(bad)


def test_T16_trace_flag_at_exact_boundary(make_link):
    # T16 (review R1): losses 0.1, 0, 1.0, 0, 0.2 dB, R = 4.7 dB, T01 otherwise. Exact M = 0:
    # NOT_EXCLUDED, TP3 above_threshold true, |headroom_db(TP3)| < 1e-9.
    losses = (0.1, 0.0, 1.0, 0.0, 0.2)
    link = make_link(channel_db=tuple((f"l{i}", v) for i, v in enumerate(losses)), reserve_db=4.7)
    report = evaluate(link)
    assert report.verdict == "NOT_EXCLUDED"
    tp3 = report.power_trace[-1]
    assert tp3.name == "TP3"
    assert tp3.above_threshold is True
    assert abs(tp3.headroom_db) < 1e-9
    # §3: headroom at TP3 equals M_net.
    assert tp3.headroom_db == report.margin_db


# Losses, penalties and reserve on a 0.1 dB grid make exact-on-paper boundaries common (the
# review found 110 of them in a small grid); a continuous strategy covers everything else.
grid_db = st.integers(min_value=0, max_value=60).map(lambda k: k / 10)
any_db = st.floats(min_value=0.0, max_value=20.0, allow_nan=False, allow_infinity=False)
level_db = st.one_of(st.integers(min_value=-100, max_value=100).map(lambda k: k / 10), any_db)


@given(
    losses=st.lists(st.one_of(grid_db, any_db), max_size=6),
    penalties=st.lists(st.one_of(grid_db, any_db), max_size=3),
    reserve=st.one_of(grid_db, any_db),
    launch=level_db,
    sensitivity=level_db,
)
def test_verdict_and_tp3_flag_always_agree(
    make_link, losses, penalties, reserve, launch, sensitivity
):
    # §3: M_net decides; above_threshold uses the same ε rule; at TP3 headroom equals M_net.
    link = make_link(
        channel_db=tuple((f"l{i}", v) for i, v in enumerate(losses)),
        penalties_db=tuple((f"p{i}", v) for i, v in enumerate(penalties)),
        reserve_db=reserve,
        launch_dbm=launch,
        sensitivity_dbm=sensitivity,
    )
    report = evaluate(link)
    tp3 = report.power_trace[-1]
    budget = report.results[2]
    assert tp3.headroom_db == report.margin_db
    assert (budget.status is Status.PASS) is tp3.above_threshold
    # The default link passes the electrical and wavelength checks, so the verdict is the budget.
    assert (report.verdict == "NOT_EXCLUDED") is tp3.above_threshold
    for point in report.power_trace:
        assert point.above_threshold is (point.headroom_db >= -EPSILON_DB)
