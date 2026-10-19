"""The oicd command line: every number it prints comes from the engine (model card §4, §8, §10,
§14.9, §15)."""

import json

import pytest

from oicd.cli import run


def test_evaluate_worked_example(capsys):
    assert run(["evaluate", "worked_example"]) == 0
    out = capsys.readouterr().out
    assert "NOT_EXCLUDED, M_net +0.4992 dB" in out  # §4
    assert "TP3" in out and "-4.0008 dBm OMA" in out


def test_evaluate_json_is_the_engine_report(capsys):
    assert run(["evaluate", "worked_example", "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["verdict"] == "NOT_EXCLUDED"
    assert report["margin_db"] == pytest.approx(0.4992, abs=1e-12)


def test_sweep_hand_cases(capsys):
    # §8: (1.0, 0) -> +0.4992, (0, +1) -> +2.4992, (2.0, -1) -> -1.5008
    assert (
        run(
            [
                "sweep",
                "worked_example",
                "--x",
                "channel[2].loss_max",
                "0",
                "2",
                "3",
                "--y",
                "tx.launch_oma_min",
                "-1",
                "1",
                "3",
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "design: +0.4992 dB at (1, 0)" in out
    assert "best:   +2.4992 dB at (0, 1)" in out
    assert "worst:  -1.5008 dB at (2, -1)" in out


def test_fanout(capsys):
    assert run(["fanout", "upstream_example"]) == 0
    assert "max fan-out 17" in capsys.readouterr().out  # §10
    assert run(["fanout", "worked_example"]) == 1


def test_twin(capsys):
    assert run(["twin", "bidi_engine"]) == 0
    out = capsys.readouterr().out
    assert "30 W / 6.4 Tbps = 4.6875 pJ/bit" in out  # §14.2
    assert "Not affiliated with or endorsed by any company" in out
    assert run(["twin", "photonic_processor", "--hypothesis", "H_out_1"]) == 0
    assert "TENSION    ptc.check_output_bits" in capsys.readouterr().out  # §15.3
    assert run(["twin", "no_such_product"]) == 1


def test_rack(capsys):
    assert run(["rack"]) == 0
    out = capsys.readouterr().out
    # §14.9
    assert "M -1.0016 dB, EXCLUDED" in out
    assert "M +1.9984 dB, NOT_EXCLUDED" in out
    assert "rack yield 0.4408" in out and "0.99999877" in out


def test_errors_exit_nonzero(capsys):
    assert run(["evaluate", "no_such_profile"]) == 1
    assert "error:" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        run(["no_such_command"])
