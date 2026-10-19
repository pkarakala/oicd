"""The adaptive block floating-point (ABFP) data path of the photonic processor in ahmed2025_nature,
re-implemented independently from its Supplementary Information and basumallik2022_abfp (model
card §15.3). This is not Lightmatter code and does not reproduce the paper's measured results.

    s_x = max|x| per 128-long block, s_w,i = max|w_i| per row and block, both rounded up to bfloat16
    y_i = (s_w,i · s_x / G) · Q_ADC{ G · Σ_j Q_7(ŵ_ij) · Q_10(x̂_j) + ν }

Q_n rounds half to even onto δ_n = 1/(2^(n−1) − 1) and clamps to [−1, 1]; the ADC has 11 bits over
±r (r = n under H_out_n, 1 under H_out_1) and ν is Gaussian, sized by the ADC's ENOB. Pure: the
random generator is passed in, so a seed fixes every result.
"""

import math
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

_FROZEN = ConfigDict(frozen=True, extra="forbid")

BLOCK = 128  # elements sharing one scale (ptc.abfp_block_len)


def levels(bits: int) -> int:
    """L = 2^(b−1) − 1: the largest code of a symmetric b-bit quantizer."""
    if bits < 2:
        raise ValueError("a symmetric quantizer needs at least 2 bits")
    return int(2 ** (bits - 1)) - 1


def bfloat16_round_up(x: float) -> float:
    """The smallest bfloat16 value ≥ x for x ≥ 0 (8 significant bits: step 2^(e−8) for
    x = m·2^e with 0.5 ≤ m < 1)."""
    if not math.isfinite(x) or x < 0:
        raise ValueError("a scale must be finite and non-negative")
    if x == 0.0:
        return 0.0
    _, e = math.frexp(x)
    step = 2.0 ** (e - 8)
    return math.ceil(x / step) * step


def _bf16_up(values: np.ndarray) -> np.ndarray:
    """bfloat16_round_up over an array of non-negative scales."""
    out = np.zeros_like(values, dtype=float)
    nz = values > 0
    _, e = np.frexp(values[nz])
    step = np.ldexp(1.0, e - 8)
    out[nz] = np.ceil(values[nz] / step) * step
    return out


def quantize_codes(normalized: np.ndarray, bits: int) -> np.ndarray:
    """Q_n as integer codes: round half to even of α·L, clamped to [−L, L]."""
    lv = levels(bits)
    return np.clip(np.rint(np.asarray(normalized, dtype=float) * lv), -lv, lv)


class Quantized(BaseModel):
    model_config = _FROZEN

    scale: float
    codes: tuple[int, ...]
    dequantized: tuple[float, ...]
    max_abs_error: float


def quantize_vector(x: list[float], bits: int, bfloat16_scale: bool = True) -> Quantized:
    """One vector with one scale s = max|x| (rounded up to bfloat16 if asked): codes, values."""
    values = np.asarray(x, dtype=float)
    scale = float(np.max(np.abs(values))) if values.size else 0.0
    if bfloat16_scale:
        scale = bfloat16_round_up(scale)
    if scale == 0.0:
        codes = np.zeros_like(values)
    else:
        codes = quantize_codes(values / scale, bits)
    deq = codes / levels(bits) * scale
    return Quantized(
        scale=scale,
        codes=tuple(int(c) for c in codes),
        dequantized=tuple(float(v) for v in deq),
        max_abs_error=float(np.max(np.abs(deq - values))) if values.size else 0.0,
    )


class PtcConfig(BaseModel):
    """Data-path parameters; defaults are the paper's (ahmed2025_nature) except where marked."""

    model_config = _FROZEN

    weight_bits: int = Field(default=7, ge=2, le=16)
    activation_bits: int = Field(default=10, ge=2, le=16)
    adc_bits: int = Field(default=11, ge=2, le=24)
    enob: float | None = Field(default=9.8, gt=0, le=24)  # None: a noiseless ADC
    gain: float = Field(default=1.86, gt=0, le=1024)
    block: int = Field(default=BLOCK, ge=1, le=4096)
    output_range: Literal["n", "1"] = "n"  # H_out_n or H_out_1 (model card §15.3)
    scale: Literal["abfp", "global"] = "abfp"  # one scale per block, or one per vector and row
    bfloat16_scales: bool = True


class MatvecStats(BaseModel):
    model_config = _FROZEN

    clipped_fraction: float  # ADC samples at the clamp


def _pad(a: np.ndarray, axis: int, block: int) -> np.ndarray:
    extra = (-a.shape[axis]) % block
    if extra == 0:
        return a
    widths = [(0, 0)] * a.ndim
    widths[axis] = (0, extra)
    return np.pad(a, widths)


def abfp_matmul(
    w: np.ndarray, x: np.ndarray, cfg: PtcConfig, rng: np.random.Generator
) -> tuple[np.ndarray, MatvecStats]:
    """y = W x through the ABFP data path. w is (m, k); x is (k,) or (k, batch)."""
    w = np.asarray(w, dtype=float)
    x = np.asarray(x, dtype=float)
    vector = x.ndim == 1
    xs = x[:, None] if vector else x
    if w.ndim != 2 or w.shape[1] != xs.shape[0]:
        raise ValueError(f"shapes {w.shape} and {x.shape} do not multiply")
    block = cfg.block  # the PTC's analog sum always spans one block
    wp = _pad(w, 1, block)
    xp = _pad(xs, 0, block)
    global_sw = np.max(np.abs(w), axis=1) if w.shape[1] else np.zeros(w.shape[0])
    global_sx = np.max(np.abs(xs), axis=0) if xs.shape[0] else np.zeros(xs.shape[1])
    lw, lx = levels(cfg.weight_bits), levels(cfg.activation_bits)
    ladc = levels(cfg.adc_bits)
    r = float(block) if cfg.output_range == "n" else 1.0
    step = r / ladc
    sigma = 0.0
    if cfg.enob is not None:
        snr_db = 6.02 * cfg.enob + 1.76
        sigma = (r / math.sqrt(2.0)) / 10.0 ** (snr_db / 20.0)
    y = np.zeros((w.shape[0], xs.shape[1]))
    clipped = 0
    total = 0
    for start in range(0, wp.shape[1], block):
        wb = wp[:, start : start + block]
        xb = xp[start : start + block, :]
        if cfg.scale == "abfp":
            sw, sx = np.max(np.abs(wb), axis=1), np.max(np.abs(xb), axis=0)
        else:  # one scale for the whole vector and the whole row
            sw, sx = global_sw, global_sx
        if cfg.bfloat16_scales:
            sw, sx = _bf16_up(sw), _bf16_up(sx)
        with np.errstate(divide="ignore", invalid="ignore"):
            wn = np.where(sw[:, None] > 0, wb / sw[:, None], 0.0)
            xn = np.where(sx[None, :] > 0, xb / sx[None, :], 0.0)
        qw = quantize_codes(wn, cfg.weight_bits) / lw
        qx = quantize_codes(xn, cfg.activation_bits) / lx
        analog = cfg.gain * (qw @ qx)  # the PTC's sum, in units of one product, times G
        if sigma > 0.0:
            analog = analog + rng.normal(0.0, sigma, size=analog.shape)
        codes = np.rint(analog / step)
        clipped += int(np.count_nonzero(np.abs(codes) > ladc))
        total += codes.size
        read = np.clip(codes, -ladc, ladc) * step
        y += (sw[:, None] * sx[None, :] / cfg.gain) * read
    stats = MatvecStats(clipped_fraction=clipped / total if total else 0.0)
    return (y[:, 0] if vector else y), stats


def relative_error(reference: np.ndarray, result: np.ndarray) -> float:
    """‖result − reference‖₂ / ‖reference‖₂."""
    denom = float(np.linalg.norm(reference))
    if denom == 0.0:
        raise ValueError("the reference is zero")
    return float(np.linalg.norm(result - reference)) / denom


def effective_bits(rel_err: float) -> float:
    """(20·log10(1/e) − 1.76) / 6.02, the ENOB form of a relative RMS error (model card §15.4)."""
    if rel_err <= 0.0:
        return math.inf
    return (20.0 * math.log10(1.0 / rel_err) - 1.76) / 6.02
