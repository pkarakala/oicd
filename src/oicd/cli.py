"""Command line: uv run oicd evaluate | sweep | fanout | twin <product> | rack.

Every number printed comes from the engine (the same functions the API serves); --json prints the
engine's canonical JSON instead of the summary.
"""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel

from oicd.profiles import load_link, profile_path
from oicd.report import evaluate
from oicd.schema import Link
from oicd.serialize import canonical_json
from oicd.sweep import linspace, sweep
from oicd.system.rack import evaluate_rack
from oicd.twin.catalog import load_catalog
from oicd.twin.inference import evaluate_graph
from oicd.twin.physics import physics_for, rack_spec
from oicd.upstream import max_fanout

INDEPENDENCE = (
    "Independent reconstruction from public information. Not affiliated with or endorsed by "
    "Lightmatter. Product names belong to their owners."
)


def _link(source: str) -> Link:
    """A Link from a JSON file path or a profile name (profiles/<name>.json)."""
    path = Path(source)
    return load_link(path if path.suffix == ".json" or path.exists() else profile_path(source))


def _emit(model: BaseModel, as_json: bool, summary: list[str]) -> None:
    if as_json:
        print(canonical_json(model))
    else:
        print("\n".join(summary))


def _evaluate(args: argparse.Namespace) -> int:
    report = evaluate(_link(args.link))
    lines = [f"{report.link_name}: {report.verdict}, M_net {report.margin_db:+.4f} dB"]
    lines += [
        f"  {p.name:<28} {p.power_dbm:+9.4f} dBm OMA  headroom {p.headroom_db:+.4f} dB"
        for p in report.power_trace
    ]
    lines += [
        f"  {r.status.value.upper():<5} {r.constraint.value}: {r.message}" for r in report.results
    ]
    if report.upstream is not None:
        lines.append(
            f"  upstream: {report.upstream.derivation}; max fan-out {report.upstream.max_fanout}"
        )
    _emit(report, args.json, lines)
    return 0


def _sweep(args: argparse.Namespace) -> int:
    xs = linspace(args.x[1], args.x[2], int(args.x[3]))
    ys = linspace(args.y[1], args.y[2], int(args.y[3]))
    result = sweep(_link(args.link), args.x[0], xs, args.y[0], ys)
    lines = [
        f"sweep {result.x.path} ({result.x.unit}) × {result.y.path} ({result.y.unit}): "
        f"{len(xs)} × {len(ys)} cells",
        *(
            f"  {name:<7} {c.margin_db:+.4f} dB at ({c.x:g}, {c.y:g})"
            for name, c in (
                ("design:", result.design),
                ("best:", result.best),
                ("worst:", result.worst),
            )
        ),
        f"  0 dB contour: {len(result.contour_0db)} segments",
    ]
    _emit(result, args.json, lines)
    return 0


def _fanout(args: argparse.Namespace) -> int:
    link = _link(args.link)
    if link.tx.upstream is None:
        print("error: the link has a fixed TP2; fan-out needs an upstream chain", file=sys.stderr)
        return 1
    n = max_fanout(link)
    report = evaluate(link)
    print(
        f"{report.link_name}: max fan-out {n} (1:{link.tx.upstream.split_n.value} now, "
        f"M_net {report.margin_db:+.4f} dB, {report.verdict})"
    )
    return 0


def _twin(args: argparse.Namespace) -> int:
    catalog = load_catalog()
    if args.product not in catalog.files:
        print(
            f"error: no catalog product {args.product!r}; products: "
            f"{', '.join(sorted(catalog.files))}",
            file=sys.stderr,
        )
        return 1
    graph = evaluate_graph(catalog, args.product, hypotheses=tuple(args.hypothesis))
    if args.json:
        print(canonical_json(graph))
        return 0
    info = catalog.files[args.product].product
    print(f"{info.name} ({info.status})")
    print(INDEPENDENCE)
    for n in graph.nodes:
        if n.kind == "derived" and n.file == args.product:
            print(f"  [{n.source_class.value}] {n.label}: {n.derivation}")
    for c in graph.checks:
        print(f"  {c.status:<10} {c.id}: {c.explanation}")
    for conflict in graph.conflicts:
        a, b = f"{conflict.a} ({conflict.value_a})", f"{conflict.b} ({conflict.value_b})"
        print(f"  CONFLICT  {a} against {b}")
    physics = physics_for(catalog, args.product)
    for section in physics.sections if physics else ():
        print(f"  physics: {section.title}" + (f" [{section.verdict}]" if section.verdict else ""))
        for item in section.items:
            value = f"{item.value:g}" if isinstance(item.value, float) else item.value
            print(f"    {item.label}: {value} {item.unit}".rstrip())
    return 0


def _rack(args: argparse.Namespace) -> int:
    result = evaluate_rack(rack_spec(load_catalog()))
    lines = [f"{result.name} (an OICD design, SYNTHETIC)", INDEPENDENCE]
    lines += [
        f"  {s.hypothesis}: {s.ou_used} of {s.ou_available} OU, fits {s.fits}" for s in result.space
    ]
    lines.append(
        f"  {result.xpus} XPUs, {result.links} links, {result.bidi_fibers} BiDi fibers "
        f"({result.duplex_fibers} duplex), {result.guide_dr_total:g} Guide DR"
    )
    for p in result.paths:
        where = (
            "in the module"
            if p.vclick_loss_db is None
            else f"{p.vclick_loss_db:g} dB in the channel"
        )
        lines.append(
            f"  worst path, vClick {where}: IL {p.channel_il_db:.4f} dB, "
            f"M {p.report.margin_db:+.4f} dB, {p.report.verdict}"
        )
    lines += [
        f"  link yield {y.link_yield:g} -> rack yield {y.rack_yield:.4f}" for y in result.yields
    ]
    lines.append(
        f"  a {result.rack_yield_target:g} rack needs per-link yield {result.link_yield_needed:.8f}"
    )
    _emit(result, args.json, lines)
    return 0


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(prog="oicd", description="OICD feasibility engine and twin")
    sub = top.add_subparsers(dest="command", required=True)
    p = sub.add_parser("evaluate", help="evaluate a link (JSON file or profile name)")
    p.add_argument("link")
    p.add_argument("--json", action="store_true")
    p.set_defaults(run=_evaluate)
    p = sub.add_parser("sweep", help="margin over two inputs (model card §8)")
    p.add_argument("link")
    p.add_argument("--x", nargs=4, required=True, metavar=("PATH", "START", "STOP", "NUM"))
    p.add_argument("--y", nargs=4, required=True, metavar=("PATH", "START", "STOP", "NUM"))
    p.add_argument("--json", action="store_true")
    p.set_defaults(run=_sweep)
    p = sub.add_parser("fanout", help="maximum laser fan-out of an upstream chain (§10)")
    p.add_argument("link")
    p.set_defaults(run=_fanout)
    p = sub.add_parser("twin", help="a product twin: derivations, checks, conflicts, physics")
    p.add_argument("product")
    p.add_argument("--hypothesis", action="append", default=[], metavar="H_ID")
    p.add_argument("--json", action="store_true")
    p.set_defaults(run=_twin)
    p = sub.add_parser("rack", help="the reference rack OICD-R64 (§14.9)")
    p.add_argument("--json", action="store_true")
    p.set_defaults(run=_rack)
    return top


def _coerce_axes(args: argparse.Namespace) -> None:
    for axis in ("x", "y"):
        values = getattr(args, axis, None)
        if values is not None:
            setattr(args, axis, [values[0], float(values[1]), float(values[2]), int(values[3])])


def run(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    _coerce_axes(args)
    try:
        code: int = args.run(args)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        message = exc.args[0] if isinstance(exc, KeyError) and exc.args else exc
        print(f"error: {message}", file=sys.stderr)
        return 1
    return code
