"""Seeded experiments on the ABFP data path (model card §15.4). Inputs are SYNTHETIC (Gaussian and
Student-t data, a Gaussian-mixture classification set); results are INFERENCE about this
re-implementation, never the paper's measured Table 1. Pure: every function takes its seed.
"""

import numpy as np
from pydantic import BaseModel, ConfigDict

from oicd.compute.ptc import PtcConfig, abfp_matmul, effective_bits, relative_error

_FROZEN = ConfigDict(frozen=True, extra="forbid")

GAINS = (1.0, 1.86, 4.0, 8.0)  # 1.86 measured, 4 the design target (ahmed2025_nature)
MLP_GAINS = (0.1, 0.25, 0.5, 1.0, 1.86, 4.0, 8.0)
LENGTHS = (128, 256, 512, 1024)
ENOBS = (6.0, 8.0, 9.8, 11.0)


class ErrorRow(BaseModel):
    model_config = _FROZEN

    length: int
    gain: float
    enob: float | None
    scale: str
    distribution: str
    relative_error: float
    effective_bits: float
    clipped_fraction: float


def matvec_error(
    length: int,
    gain: float,
    enob: float | None,
    seed: int,
    rows: int = 64,
    trials: int = 8,
    scale: str = "abfp",
    distribution: str = "gaussian",
    output_range: str = "n",
) -> ErrorRow:
    """Relative RMS error of y = Wx over `trials` vectors, against the float64 product."""
    cfg = PtcConfig(gain=gain, enob=enob, scale=scale, output_range=output_range)  # type: ignore[arg-type]
    return matvec_error_for(cfg, length, seed, rows, trials, distribution)


def matvec_error_for(
    cfg: PtcConfig,
    length: int,
    seed: int,
    rows: int = 64,
    trials: int = 8,
    distribution: str = "gaussian",
) -> ErrorRow:
    """matvec_error for any data-path configuration (the API's simulator)."""
    rng = np.random.default_rng(seed)
    w = rng.normal(size=(rows, length))
    if distribution == "student_t":
        x = rng.standard_t(3, size=(length, trials))
    else:
        x = rng.normal(size=(length, trials))
    y, stats = abfp_matmul(w, x, cfg, np.random.default_rng(seed + 1))
    err = relative_error(w @ x, y)
    return ErrorRow(
        length=length,
        gain=cfg.gain,
        enob=cfg.enob,
        scale=cfg.scale,
        distribution=distribution,
        relative_error=err,
        effective_bits=effective_bits(err),
        clipped_fraction=stats.clipped_fraction,
    )


def error_sweeps(seed: int = 0) -> dict[str, tuple[ErrorRow, ...]]:
    """Error versus vector length, gain and ENOB (the other two at 128 / 1.86 / 9.8)."""
    return {
        "length": tuple(matvec_error(n, 1.86, 9.8, seed) for n in LENGTHS),
        "gain": tuple(matvec_error(128, g, 9.8, seed) for g in (*GAINS, 32.0, 128.0)),
        "enob": tuple(matvec_error(128, 1.86, e, seed) for e in ENOBS),
        "scale": tuple(
            matvec_error(1024, 4.0, 9.8, seed, scale=s, distribution=d)
            for d in ("gaussian", "student_t")
            for s in ("abfp", "global")
        ),
    }


class MlpResult(BaseModel):
    model_config = _FROZEN

    float_accuracy: float
    gains: tuple[float, ...]
    abfp_accuracy: tuple[float, ...]
    n_train: int
    n_test: int
    epochs: int
    seed: int


def _dataset(rng: np.random.Generator, n: int, dims: int, classes: int, spread: float):
    means = rng.normal(scale=spread, size=(classes, dims))
    labels = rng.integers(0, classes, size=n)
    x = means[labels] + rng.normal(size=(n, dims))
    return x, labels


def _forward(params, x, matmul):
    h = x
    for i, (w, b) in enumerate(params):
        h = matmul(w, h.T).T + b
        if i < len(params) - 1:
            h = np.maximum(h, 0.0)
    return h


def train_mlp(
    seed: int = 0,
    dims: int = 128,
    hidden: int = 128,
    classes: int = 10,
    n_train: int = 2000,
    n_test: int = 1000,
    epochs: int = 150,
    spread: float = 0.35,
):
    """A 3-layer ReLU MLP trained full-batch with Adam in float64 on a Gaussian mixture."""
    rng = np.random.default_rng(seed)
    x_all, y_all = _dataset(rng, n_train + n_test, dims, classes, spread)
    x_tr, y_tr = x_all[:n_train], y_all[:n_train]
    x_te, y_te = x_all[n_train:], y_all[n_train:]
    sizes = [dims, hidden, hidden, classes]
    params = [
        (rng.normal(scale=np.sqrt(2.0 / a), size=(b, a)), np.zeros(b))
        for a, b in zip(sizes[:-1], sizes[1:], strict=True)
    ]
    m = [(np.zeros_like(w), np.zeros_like(b)) for w, b in params]
    v = [(np.zeros_like(w), np.zeros_like(b)) for w, b in params]
    lr, b1, b2, eps = 3e-3, 0.9, 0.999, 1e-8
    onehot = np.eye(classes)[y_tr]
    for t in range(1, epochs + 1):
        acts = [x_tr]
        h = x_tr
        for i, (w, b) in enumerate(params):
            h = h @ w.T + b
            if i < len(params) - 1:
                h = np.maximum(h, 0.0)
            acts.append(h)
        logits = acts[-1]
        p = np.exp(logits - logits.max(axis=1, keepdims=True))
        p /= p.sum(axis=1, keepdims=True)
        grad = (p - onehot) / len(x_tr)
        for i in range(len(params) - 1, -1, -1):
            w, b = params[i]
            gw = grad.T @ acts[i]
            gb = grad.sum(axis=0)
            if i > 0:
                grad = (grad @ w) * (acts[i] > 0)
            mw, mb = m[i]
            vw, vb = v[i]
            mw = b1 * mw + (1 - b1) * gw
            mb = b1 * mb + (1 - b1) * gb
            vw = b2 * vw + (1 - b2) * gw**2
            vb = b2 * vb + (1 - b2) * gb**2
            m[i], v[i] = (mw, mb), (vw, vb)
            c1, c2 = 1 - b1**t, 1 - b2**t
            params[i] = (
                w - lr * (mw / c1) / (np.sqrt(vw / c2) + eps),
                b - lr * (mb / c1) / (np.sqrt(vb / c2) + eps),
            )
    return params, (x_te, y_te)


def mlp_accuracy_vs_gain(seed: int = 0, gains: tuple[float, ...] = MLP_GAINS, **sizes) -> MlpResult:
    """Accuracy of the float64-trained MLP when every matrix-vector product runs through ABFP."""
    params, (x_te, y_te) = train_mlp(seed=seed, **sizes)
    exact = _forward(params, x_te, lambda w, h: w @ h)
    float_acc = float(np.mean(exact.argmax(axis=1) == y_te))
    accs = []
    for g in gains:
        rng = np.random.default_rng(seed + 7)
        cfg = PtcConfig(gain=g)

        def matmul(w, h, cfg=cfg, rng=rng):
            return abfp_matmul(w, h, cfg, rng)[0]

        out = _forward(params, x_te, matmul)
        accs.append(float(np.mean(out.argmax(axis=1) == y_te)))
    return MlpResult(
        float_accuracy=float_acc,
        gains=tuple(gains),
        abfp_accuracy=tuple(accs),
        n_train=sizes.get("n_train", 2000),
        n_test=sizes.get("n_test", 1000),
        epochs=sizes.get("epochs", 150),
        seed=seed,
    )
