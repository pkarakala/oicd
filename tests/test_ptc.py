"""Model card §15.3 and §15.4: the ABFP data path and its seeded experiments."""

import math

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from oicd.compute.experiments import matvec_error, mlp_accuracy_vs_gain
from oicd.compute.ptc import (
    PtcConfig,
    abfp_matmul,
    bfloat16_round_up,
    effective_bits,
    levels,
    quantize_codes,
    quantize_vector,
    relative_error,
)

X = [0.3, -1.2, 0.05, 0.9]


def test_hand_case_exact_scale():
    # §15.3: s = 1.2, b = 7 -> codes [16, -63, 3, 47], max abs error 0.007143
    q = quantize_vector(X, 7, bfloat16_scale=False)
    assert q.scale == 1.2
    assert q.codes == (16, -63, 3, 47)
    assert q.dequantized == pytest.approx((0.304762, -1.2, 0.057143, 0.895238), abs=5e-7)
    assert q.max_abs_error == pytest.approx(0.007143, abs=5e-7)


def test_hand_case_bfloat16_scale():
    # §15.3: 1.2 -> 1.203125 in bfloat16 (rounded up); the same codes
    q = quantize_vector(X, 7)
    assert q.scale == 1.203125
    assert q.codes == (16, -63, 3, 47)
    assert q.dequantized == pytest.approx((0.305556, -1.203125, 0.057292, 0.897569), abs=5e-7)
    assert q.max_abs_error == pytest.approx(0.007292, abs=5e-7)


def test_levels_and_rounding():
    assert (levels(7), levels(10), levels(11)) == (63, 511, 1023)
    # round half to even (basumallik2022_abfp), clamp to [-L, L]
    lv = levels(7)
    assert quantize_codes(np.array([2.5, 3.5, -2.5]) / lv, 7).tolist() == [2, 4, -2]
    assert quantize_codes(np.array([1.5, -3.0]), 7).tolist() == [63, -63]
    with pytest.raises(ValueError):
        levels(1)


@given(st.floats(min_value=1e-30, max_value=1e30, allow_nan=False))
def test_bfloat16_round_up_is_the_next_representable_value(x):
    up = bfloat16_round_up(x)
    _, e = math.frexp(up)
    step = 2.0 ** (e - 8)
    assert up >= x
    assert up / step == pytest.approx(round(up / step))  # 8 significant bits
    assert up - 2.0 ** (math.frexp(x)[1] - 8) < x  # nothing representable in between


def test_bfloat16_edges():
    assert bfloat16_round_up(0.0) == 0.0
    assert bfloat16_round_up(1.0) == 1.0
    with pytest.raises(ValueError):
        bfloat16_round_up(-1.0)


def test_effective_bits_inverts_the_enob_formula():
    for bits in (4.0, 9.8):
        e = 10 ** (-(6.02 * bits + 1.76) / 20)
        assert effective_bits(e) == pytest.approx(bits)


def test_wide_and_noiseless_path_is_exact():
    rng = np.random.default_rng(3)
    w, x = rng.normal(size=(16, 300)), rng.normal(size=300)
    cfg = PtcConfig(weight_bits=16, activation_bits=16, adc_bits=24, enob=None, gain=1.0)
    y, stats = abfp_matmul(w, x, cfg, rng)
    assert relative_error(w @ x, y) < 1e-4
    assert stats.clipped_fraction == 0.0


def test_seeded_and_shape_checked():
    a = matvec_error(256, 1.86, 9.8, seed=5)
    b = matvec_error(256, 1.86, 9.8, seed=5)
    assert a == b
    with pytest.raises(ValueError):
        abfp_matmul(np.ones((2, 3)), np.ones(4), PtcConfig(), np.random.default_rng(0))


def test_gain_trades_resolution_for_clipping():
    # §15.4: error falls from G = 1 to the design target 4, until clipping sets in
    e = {g: matvec_error(128, g, 9.8, seed=0) for g in (1.0, 1.86, 4.0, 128.0)}
    assert e[1.0].relative_error > e[1.86].relative_error > e[4.0].relative_error
    assert e[4.0].clipped_fraction == 0.0
    assert e[128.0].clipped_fraction > 0.1 and e[128.0].relative_error > e[1.0].relative_error


def test_error_falls_with_enob():
    enobs = (6.0, 8.0, 9.8, 11.0)
    errors = [matvec_error(128, 1.86, enob, seed=0).relative_error for enob in enobs]
    assert errors == sorted(errors, reverse=True)


def test_block_scales_beat_a_global_scale_on_outliers():
    abfp = matvec_error(1024, 4.0, 9.8, seed=0, distribution="student_t")
    glob = matvec_error(1024, 4.0, 9.8, seed=0, distribution="student_t", scale="global")
    assert abfp.relative_error < glob.relative_error


def test_literal_si_range_clips():
    # H_out_1: the [-1, 1] clamp on the 128-term sum clips most sums
    row = matvec_error(128, 1.86, 9.8, seed=0, output_range="1")
    assert row.clipped_fraction > 0.5 and row.relative_error > 0.5


def test_mlp_accuracy_rises_with_gain():
    r = mlp_accuracy_vs_gain(seed=0, n_train=800, n_test=600, epochs=80)
    acc = dict(zip(r.gains, r.abfp_accuracy, strict=True))
    assert acc[0.1] < acc[1.86] - 0.1
    assert acc[4.0] >= r.float_accuracy - 0.02
