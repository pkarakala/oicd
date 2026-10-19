"""Regenerate every figure in docs/figures/ (PDF and PNG), deterministically.

Every plotted number is computed by the engine (oicd); colors come from oicd.display, the same
palette the explorer uses. Run: uv run python scripts/make_figures.py [--check]
(--check renders into a temporary directory and leaves docs/figures alone).
"""

import argparse
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from oicd.compute.experiments import error_sweeps, mlp_accuracy_vs_gain  # noqa: E402
from oicd.display import margin_color, palette  # noqa: E402
from oicd.physics import ring, wdm  # noqa: E402
from oicd.profiles import load_link, profile_path  # noqa: E402
from oicd.report import evaluate  # noqa: E402
from oicd.statistics import analytic_yield  # noqa: E402
from oicd.sweep import linspace, sweep  # noqa: E402
from oicd.system.rack import evaluate_rack  # noqa: E402
from oicd.twin.catalog import load_catalog  # noqa: E402
from oicd.twin.inference import evaluate_graph  # noqa: E402
from oicd.twin.physics import rack_spec  # noqa: E402
from oicd.upstream import max_fanout, with_split  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "figures"
P = palette("light")
STATUS = {s.key: s.color for s in P.status}
CLASS = {c.key: c.color for c in P.classes}
INK, MUTED, GRID = P.ink, P.muted, P.grid
FOOT = "OICD (independent reconstruction from public information; not affiliated with Lightmatter)"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": INK,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "xtick.color": INK,
        "ytick.color": INK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 150,
        "savefig.bbox": "tight",
        "svg.hashsalt": "oicd",
    }
)


def _footer(fig: plt.Figure, source: str) -> None:
    fig.text(0.01, -0.02, f"{source}. {FOOT}", fontsize=6.5, color=MUTED, ha="left", va="top")


def fig_waterfall(fig: plt.Figure) -> str:
    report = evaluate(load_link(profile_path("worked_example")))
    ax = fig.add_subplot()
    trace = report.power_trace
    x = np.arange(len(trace))
    ax.step(x, [p.power_dbm for p in trace], where="mid", color=INK, linewidth=1.5)
    for i, p in enumerate(trace):
        color = STATUS["NOT_EXCLUDED"] if p.above_threshold else STATUS["EXCLUDED"]
        ax.plot(i, p.power_dbm, "o", color=color, markersize=6, zorder=3)
    ax.axhline(report.threshold_dbm, color=MUTED, linestyle="--", linewidth=1)
    ax.annotate(
        f"threshold {report.threshold_dbm:.4f} dBm",
        (0, report.threshold_dbm),
        xytext=(0, -12),
        textcoords="offset points",
        color=MUTED,
        fontsize=8,
    )
    ax.annotate(
        f"M_net {report.margin_db:+.4f} dB",
        (x[-1], trace[-1].power_dbm),
        xytext=(-80, 18),
        textcoords="offset points",
        fontsize=8,
        arrowprops={"arrowstyle": "->", "color": INK},
    )
    ax.set_xticks(x, [p.name for p in trace], rotation=30, ha="right")
    ax.set_ylabel("OMA (dBm)")
    ax.set_title("Power waterfall, model card §4 worked example", loc="left")
    _footer(fig, "Model card §3, §4")
    return "power_waterfall"


def fig_sweep(fig: plt.Figure) -> str:
    link = load_link(profile_path("worked_example"))
    xs, ys = linspace(0.0, 3.0, 61), linspace(-2.0, 2.0, 41)
    result = sweep(link, "channel[2].loss_max", xs, "tx.launch_oma_min", ys)
    ax = fig.add_subplot()
    m = np.array(result.margin_db)
    bins = P.margin_bins
    edges = [-1e9] + [b.hi_db for b in bins[:-1]] + [1e9]
    cmap = matplotlib.colors.ListedColormap([b.color for b in bins])
    norm = matplotlib.colors.BoundaryNorm([e if e is not None else 0 for e in edges], cmap.N)
    mesh = ax.pcolormesh(xs, ys, m, cmap=cmap, norm=norm, shading="nearest")
    for (x0, y0), (x1, y1) in result.contour_0db:
        ax.plot([x0, x1], [y0, y1], color=INK, linewidth=1.6)
    ax.plot(result.design.x, result.design.y, "x", color=INK, markersize=9, markeredgewidth=2)
    ax.annotate(
        f"design {result.design.margin_db:+.4f} dB",
        (result.design.x, result.design.y),
        xytext=(8, 8),
        textcoords="offset points",
        fontsize=8,
    )
    bar = fig.colorbar(mesh, ax=ax, ticks=[-3, -1.5, 0, 1.5, 3])
    bar.set_label("M_net (dB)")
    ax.set_xlabel("patch connector loss (dB)")
    ax.set_ylabel("TX launch OMA (dBm)")
    ax.set_title("Design space with the engine's 0 dB contour (model card §8)", loc="left")
    _footer(fig, "Model card §8")
    return "sweep"


def fig_fanout(fig: plt.Figure) -> str:
    link = load_link(profile_path("upstream_example"))
    ns = list(range(1, 33))
    margins = [evaluate(with_split(link, n)).margin_db for n in ns]
    best = max_fanout(link)
    ax = fig.add_subplot()
    ax.plot(ns, margins, color=CLASS["inference"], linewidth=1.6, marker="o", markersize=3)
    ax.axhline(0, color=INK, linewidth=1)
    ax.axvline(best, color=MUTED, linestyle="--", linewidth=1)
    ax.annotate(
        f"max fan-out {best}", (best, 0), xytext=(6, 30), textcoords="offset points", fontsize=8
    )
    ax.set_xlabel("laser split 1:N")
    ax.set_ylabel("M_net (dB)")
    ax.set_title("Laser fan-out margin, model card §10 chain (SYNTHETIC inputs)", loc="left")
    _footer(fig, "Model card §10")
    return "fanout"


def fig_yield_connectors(fig: plt.Figure) -> str:
    base = load_link(profile_path("yield_example"))
    counts = list(range(0, 7))
    worst, yields = [], []
    for n in counts:
        data = base.model_dump()
        data["channel"] = list(data["channel"])
        patch = data["channel"][2]
        for k in range(n):
            extra = {**patch, "name": f"added connector {k + 1}"}
            extra["loss_max"] = {**patch["loss_max"], "value": {"value": 0.5}}
            extra["loss_distribution"] = {
                "mean": {**patch["loss_max"], "value": {"value": 0.5}},
                "sigma": patch["loss_distribution"]["sigma"],
            }
            data["channel"].insert(3, extra)
        result = analytic_yield(type(base).model_validate(data))
        worst.append(result.worst_case_margin_db)
        yields.append(result.yield_fraction)
    ax1, ax2 = fig.subplots(1, 2)
    ax1.plot(counts, worst, marker="o", color=INK)
    ax1.axhline(0, color=STATUS["EXCLUDED"], linewidth=1)
    ax1.set_xlabel("added 0.5 dB connectors")
    ax1.set_ylabel("worst-case M_net (dB)")
    ax1.set_title("Worst case", loc="left")
    ax2.plot(counts, [100 * y for y in yields], marker="o", color=CLASS["inference"])
    ax2.set_xlabel("added 0.5 dB connectors (σ 0.2 dB each)")
    ax2.set_ylabel("yield P(M_net ≥ 0) (%)")
    ax2.set_title("Statistical, assumption-dependent", loc="left")
    fig.suptitle(
        "Stacking connectors: worst case against yield (model card §11)", x=0.01, ha="left"
    )
    _footer(fig, "Model card §11")
    return "yield_vs_connectors"


def fig_q_window(fig: plt.Figure) -> str:
    f0 = ring.resonance_frequency_ghz(1310.0)
    rates = np.linspace(20.0, 120.0, 101)
    ax = fig.add_subplot()
    for spacing, color in ((200.0, CLASS["inference"]), (400.0, CLASS["vendor_claim"])):
        windows = [ring.design_window(f0, spacing, float(b)) for b in rates]
        q_min = windows[0].q_min
        q_max = [w.q_max for w in windows]
        ax.plot(rates, q_max, color=INK, linewidth=1.4)
        ax.axhline(q_min, color=color, linewidth=1.4, label=f"Q_min at {spacing:g} GHz")
        ax.fill_between(
            rates, q_min, q_max, where=[q > q_min for q in q_max], color=color, alpha=0.12
        )
    ax.axhline(3500, color=MUTED, linestyle="--", linewidth=1)
    ax.annotate(
        "Q 3500 (OFC 2025 ring)",
        (rates[0], 3500),
        xytext=(4, 4),
        textcoords="offset points",
        fontsize=8,
        color=MUTED,
    )
    for b in (56.0, 106.25):
        ax.axvline(b, color=GRID, linewidth=1)
    ax.set_xlabel("symbol rate (GBd)")
    ax.set_ylabel("loaded Q")
    ax.set_ylim(0, 9000)
    ax.legend(frameon=False, loc="upper right")
    ax.set_title(
        "Ring design window: −15 dB per neighbor, f0/Q ≥ 0.75 × rate (SYNTHETIC rules)", loc="left"
    )
    _footer(fig, "Model card §13.3")
    return "q_design_window"


def fig_interleave(fig: plt.Figure) -> str:
    f0 = ring.resonance_frequency_ghz(1310.0)
    fwhm = ring.fwhm_ghz(f0, 3500.0)
    detune = np.linspace(-700.0, 700.0, 1401)
    ax = fig.add_subplot()
    ax.plot(detune, [ring.db(ring.lorentzian(float(d), fwhm)) for d in detune], color=INK)
    for spacing, color in ((200.0, CLASS["vendor_claim"]), (400.0, CLASS["inference"])):
        level = ring.db(ring.lorentzian(spacing, fwhm))
        ax.plot([spacing, -spacing], [level, level], "o", color=color, markersize=6)
        ax.annotate(
            f"{spacing:g} GHz: {level:.3f} dB",
            (spacing, level),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=8,
        )
    ax.set_xlabel("detuning from the ring (GHz)")
    ax.set_ylabel("drop response (dB)")
    ax.set_title(
        "Interleaving: a co-directional neighbor at 400 GHz instead of 200 GHz (Q 3500)", loc="left"
    )
    _footer(fig, "Model card §13.1, §13.8")
    return "interleave_crosstalk"


def fig_bidi16(fig: plt.Figure) -> str:
    catalog = load_catalog()
    v = {
        i: catalog.nodes[i].nominal
        for i in (
            "bidi16.center_nm",
            "bidi16.txrx_spacing_ghz",  # type: ignore[union-attr]
            "bidi16.lambda_count",
            "ring.mrm_q",
            "bidi16.channel_loss",
            "bidi16.return_loss_db",
        )
    }
    grid = wdm.interleaved_grid(
        v["bidi16.center_nm"], v["bidi16.txrx_spacing_ghz"], int(v["bidi16.lambda_count"])
    )
    fwhm = ring.fwhm_ghz(ring.resonance_frequency_ghz(v["bidi16.center_nm"]), v["ring.mrm_q"])
    count = int(v["bidi16.lambda_count"])
    receive, transmit = tuple(range(1, count, 2)), tuple(range(0, count, 2))
    axes = fig.subplots(1, 2, sharey=True)
    for ax, h in zip(axes, ("H_fsr18", "H_fsr32"), strict=True):
        fsr = catalog.hypotheses[h].sets["bidi16.ring_fsr_thz"] * 1000.0
        rings = [
            wdm.ring_leakage(
                grid,
                n,
                fwhm,
                fsr,
                receive,
                transmit,
                "NRZ",
                v["bidi16.channel_loss"],
                v["bidi16.return_loss_db"],
            )
            for n in receive
        ]
        worst = wdm.worst_channel(grid, rings)
        colors = [
            STATUS["EXCLUDED"] if r.channel == worst.channel else CLASS["inference"] for r in rings
        ]
        ax.bar([str(r.channel) for r in rings], [r.crosstalk_db for r in rings], color=colors)
        ax.set_title(f"{h}: FSR {fsr / 1000:g} THz, worst channel {worst.channel}", loc="left")
        ax.set_xlabel("receive channel n")
    axes[0].set_ylabel("co-directional crosstalk penalty, NRZ (dB)")
    fig.suptitle(
        "16λ BiDi receive rings under the two ring-FSR hypotheses (INFERENCE)", x=0.01, ha="left"
    )
    _footer(fig, "Model card §13.6, §14.5")
    return "bidi16_crosstalk"


def fig_rack_planes(fig: plt.Figure) -> str:
    result = evaluate_rack(rack_spec(load_catalog()))
    labels, margins = [], []
    for p in result.paths:
        labels.append(
            "vClick in module"
            if p.vclick_loss_db is None
            else f"vClick {p.vclick_loss_db:g} dB in channel"
        )
        margins.append(p.report.margin_db)
    ax = fig.add_subplot()
    bars = ax.bar(labels, margins, color=[margin_color(m) for m in margins])
    ax.axhline(0, color=INK, linewidth=1)
    for bar, m, p in zip(bars, margins, result.paths, strict=True):
        ax.annotate(
            f"{m:+.4f} dB\n{p.report.verdict}",
            (bar.get_x() + bar.get_width() / 2, m),
            xytext=(0, 4 if m >= 0 else -24),
            textcoords="offset points",
            ha="center",
            fontsize=8,
        )
    ax.set_ylabel("worst-path M_net on the draft DR budget (dB)")
    ax.set_title(
        "Reference rack OICD-R64: the reference plane decides (SYNTHETIC design)", loc="left"
    )
    _footer(fig, "Model card §14.9")
    return "rack_reference_planes"


def fig_rack_yield(fig: plt.Figure) -> str:
    result = evaluate_rack(rack_spec(load_catalog()))
    q = np.logspace(-7, -3, 200)  # 1 − link yield
    ax = fig.add_subplot()
    ax.plot(q, (1 - q) ** result.links, color=CLASS["inference"], linewidth=1.6)
    ax.axhline(result.rack_yield_target, color=MUTED, linestyle="--", linewidth=1)
    ax.axvline(1 - result.link_yield_needed, color=MUTED, linestyle="--", linewidth=1)
    ax.annotate(
        f"needs link yield {result.link_yield_needed:.8f}",
        (1 - result.link_yield_needed, result.rack_yield_target),
        xytext=(8, -20),
        textcoords="offset points",
        fontsize=8,
    )
    for row in result.yields:
        ax.plot(1 - row.link_yield, row.rack_yield, "o", color=INK)
        ax.annotate(
            f"y {row.link_yield:g}: {row.rack_yield:.4f}",
            (1 - row.link_yield, row.rack_yield),
            xytext=(6, 4),
            textcoords="offset points",
            fontsize=8,
        )
    ax.set_xscale("log")
    ax.invert_xaxis()
    ax.set_xlabel("1 − per-link yield")
    ax.set_ylabel(f"rack yield, all {result.links} links pass")
    ax.set_title("Rack yield against per-link yield (independent links)", loc="left")
    _footer(fig, "Model card §14.9")
    return "rack_yield"


def fig_support(fig: plt.Figure) -> str:
    graph = evaluate_graph(load_catalog(), "ocp_trays")
    checks = [c.id for c in graph.checks]
    rows = graph.support
    code = {"CONSISTENT": 0, "TENSION": 1, "CONFLICT": 2}
    data = np.array([[code[r.cells[c].status] for c in checks] for r in rows])
    cmap = matplotlib.colors.ListedColormap(
        [STATUS["CONSISTENT"], STATUS["TENSION"], STATUS["CONFLICT"]]
    )
    ax = fig.add_subplot()
    ax.imshow(data, cmap=cmap, vmin=0, vmax=2, aspect="auto")
    sym = {0: "✓", 1: "!", 2: "✕"}
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(j, i, sym[int(data[i, j])], ha="center", va="center", fontsize=8, color="#111")
    ax.set_xticks(range(len(checks)), [c.split(".", 1)[1] for c in checks], rotation=45, ha="right")
    ax.set_yticks(range(len(rows)), [r.hypothesis for r in rows])
    ax.grid(False)
    ax.set_title(
        "OCP 2026 trays: hypotheses against checks (✓ consistent, ! tension, ✕ conflict)",
        loc="left",
    )
    _footer(fig, "Model card §14.7")
    return "support_matrix"


def fig_processor(fig: plt.Figure) -> str:
    sweeps = error_sweeps(seed=0)
    mlp = mlp_accuracy_vs_gain(seed=0)
    ax1, ax2 = fig.subplots(1, 2)
    gains = [r.gain for r in sweeps["gain"]]
    ax1.plot(
        gains,
        [100 * r.relative_error for r in sweeps["gain"]],
        marker="o",
        color=CLASS["inference"],
    )
    for g in (1.86, 4.0):
        ax1.axvline(g, color=MUTED, linestyle="--", linewidth=1)
    ax1.annotate("1.86 measured", (1.86, 30), fontsize=7, color=MUTED, rotation=90)
    ax1.annotate("4 design target", (4.0, 30), fontsize=7, color=MUTED, rotation=90)
    ax1.set_xscale("log")
    ax1.set_yscale("log")
    ax1.set_xlabel("gain G")
    ax1.set_ylabel("relative error of y = Wx (%)")
    ax1.set_title("128-long, ENOB 9.8, Gaussian data", loc="left")
    ax2.plot(mlp.gains, [100 * a for a in mlp.abfp_accuracy], marker="o", color=CLASS["inference"])
    ax2.axhline(100 * mlp.float_accuracy, color=INK, linewidth=1)
    ax2.annotate(
        "float64",
        (mlp.gains[0], 100 * mlp.float_accuracy),
        xytext=(4, 4),
        textcoords="offset points",
        fontsize=8,
    )
    ax2.set_xscale("log")
    ax2.set_xlabel("gain G")
    ax2.set_ylabel("accuracy (%)")
    ax2.set_title("3-layer MLP, synthetic 10-class set", loc="left")
    fig.suptitle(
        "ABFP data path, independent re-implementation (seeded, SYNTHETIC inputs; "
        "not the paper's Table 1)",
        x=0.01,
        ha="left",
    )
    _footer(fig, "Model card §15.4")
    return "processor_error_vs_gain"


FIGURES: tuple[tuple[Callable[[plt.Figure], str], tuple[float, float]], ...] = (
    (fig_waterfall, (6.4, 3.6)),
    (fig_sweep, (6.4, 4.2)),
    (fig_fanout, (6.4, 3.6)),
    (fig_yield_connectors, (8.0, 3.4)),
    (fig_q_window, (6.4, 4.0)),
    (fig_interleave, (6.4, 3.6)),
    (fig_bidi16, (8.4, 3.6)),
    (fig_rack_planes, (6.4, 3.8)),
    (fig_rack_yield, (6.4, 3.8)),
    (fig_support, (7.2, 3.4)),
    (fig_processor, (8.4, 3.6)),
)


def render(out: Path) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for make, size in FIGURES:
        fig = plt.figure(figsize=size)
        name = make(fig)
        for ext, meta in (("pdf", {"CreationDate": None, "ModDate": None}), ("png", {})):
            path = out / f"{name}.{ext}"
            fig.savefig(path, metadata=meta)
            written.append(path)
        plt.close(fig)
    return written


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="render into a temporary directory")
    args = parser.parse_args(argv)
    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            n = len(render(Path(tmp)))
        print(f"rendered {n} files")
        return 0
    for path in render(OUT):
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
