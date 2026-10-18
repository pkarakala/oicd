"""Inference graph evaluation (model card §14).

Every node gets a nominal value and an interval [lo, hi]. Facts are points unless the source gives
a range; assumptions span [low, high]; a derived node's interval comes from evaluating it at every
corner of its interval-valued ancestors (exact for functions monotone in each ancestor), or from a
seeded Monte Carlo when there are more than CORNER_LIMIT of them (flagged). Derived nodes are
INFERENCE and carry a derivation string such as "30 W / 6.4 Tbps = 4.6875 pJ/bit".

Checks return CONSISTENT when the gap is within tolerance, otherwise CONFLICT when both sides are
facts (two sources disagree) and TENSION when a derived node is involved (a reading or assumption
of ours disagrees with a claim). Hypotheses pin assumptions; re-evaluating under each one gives
the support matrix (hypothesis × check). The tornado ranks, per derived node, how far each
assumption moves it between its low and high values.

Pure and deterministic: the Monte Carlo uses a fixed seed.
"""

import itertools
import math
from collections.abc import Mapping
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict

from oicd.provenance import SourceClass
from oicd.twin.catalog import Assumption, Catalog, CatalogError, Check, Derived, Fact
from oicd.twin.formulas import FORMULAS, format_number, render, with_unit

_FROZEN = ConfigDict(frozen=True, extra="forbid")

CORNER_LIMIT = 12
MC_SAMPLES = 4096
MC_SEED = 20261018

Status = Literal["CONSISTENT", "TENSION", "CONFLICT"]
Method = Literal["point", "corners", "monte_carlo"]


class NodeResult(BaseModel):
    model_config = _FROZEN

    id: str
    kind: Literal["fact", "assumption", "derived"]
    label: str
    unit: str
    nominal: float | None
    lo: float | None
    hi: float | None
    source_class: SourceClass
    derivation: str
    inputs: tuple[str, ...]
    method: Method
    interval_parents: tuple[str, ...]
    flagged: bool  # Monte Carlo interval (more than CORNER_LIMIT interval ancestors)
    pinned_by: str | None  # hypothesis id or "override" when an assumption is pinned
    verified: bool | None = None
    cite: str | None = None
    quote: str | None = None
    bound: str | None = None
    file: str


class CheckOutcome(BaseModel):
    model_config = _FROZEN

    id: str
    kind: Literal["consistent", "bound"]
    a: str
    b: str
    unit: str
    a_value: float
    b_value: float
    gap_abs: float
    gap_rel: float | None  # |a − b| / |b|; None when b = 0
    rel_tol: float
    status: Status
    interval_overlap: bool
    explanation: str


class ConflictPair(BaseModel):
    model_config = _FROZEN

    a: str
    b: str
    quantity_a: str
    quantity_b: str
    quote_a: str
    quote_b: str
    cite_a: str
    cite_b: str
    value_a: str
    value_b: str


class SupportCell(BaseModel):
    model_config = _FROZEN

    status: Status
    gap_rel: float | None


class SupportRow(BaseModel):
    model_config = _FROZEN

    hypothesis: str  # "baseline" for no hypothesis
    group: str
    statement: str
    cells: dict[str, SupportCell]
    agrees: tuple[str, ...]
    disagrees: tuple[str, ...]


class TornadoBar(BaseModel):
    model_config = _FROZEN

    assumption: str
    low: float
    high: float
    value_at_low: float
    value_at_high: float
    swing: float


class TornadoEntry(BaseModel):
    model_config = _FROZEN

    node: str
    nominal: float
    bars: tuple[TornadoBar, ...]


class EvaluatedGraph(BaseModel):
    model_config = _FROZEN

    scope: str
    hypotheses: tuple[str, ...]
    overrides: dict[str, float]
    nodes: tuple[NodeResult, ...]
    checks: tuple[CheckOutcome, ...]
    conflicts: tuple[ConflictPair, ...]
    support: tuple[SupportRow, ...]
    tornado: tuple[TornadoEntry, ...]


def _fact_value_text(f: Fact) -> str:
    if f.value is not None:
        return with_unit(f.value, f.unit)
    if f.lo is not None and f.hi is not None:
        return f"{format_number(f.lo)} to {with_unit(f.hi, f.unit)}"
    return f.quantity


class _Graph:
    """One evaluation of the catalog with fixed pins (overrides and hypothesis settings)."""

    def __init__(self, catalog: Catalog, pins: Mapping[str, tuple[float, str]]):
        self.catalog = catalog
        self.pins = pins

    def leaf_interval(self, node_id: str) -> tuple[float, float, float]:
        """(nominal, lo, hi) of a fact or assumption under the pins."""
        node = self.catalog.nodes[node_id]
        if node_id in self.pins:
            v = self.pins[node_id][0]
            return v, v, v
        if isinstance(node, Assumption):
            return node.nominal, node.low, node.high
        if isinstance(node, Fact):
            if node.lo is not None and node.hi is not None:
                return node.nominal, node.lo, node.hi
            return node.nominal, node.nominal, node.nominal
        raise CatalogError(f"{node_id} is not a leaf")

    def interval_leaves(self, node_id: str, memo: dict[str, frozenset[str]]) -> frozenset[str]:
        if node_id in memo:
            return memo[node_id]
        node = self.catalog.nodes[node_id]
        if isinstance(node, Derived):
            out = frozenset().union(*(self.interval_leaves(i, memo) for i in node.inputs))
        else:
            _, lo, hi = self.leaf_interval(node_id)
            out = frozenset({node_id}) if lo < hi else frozenset()
        memo[node_id] = out
        return out

    def value(self, node_id: str, leaves: Mapping[str, float], cache: dict[str, float]) -> float:
        """The node's value with the given leaf values (others at nominal)."""
        if node_id in cache:
            return cache[node_id]
        node = self.catalog.nodes[node_id]
        if isinstance(node, Derived):
            args = [self.value(i, leaves, cache) for i in node.inputs]
            try:
                result = float(FORMULAS[node.fn].fn(*args))
            except (ArithmeticError, ValueError) as exc:
                raise CatalogError(f"{node_id}: {node.fn}{tuple(args)} failed: {exc}") from exc
            if not math.isfinite(result):
                raise CatalogError(f"{node_id}: {node.fn}{tuple(args)} is not finite")
        else:
            result = leaves.get(node_id, self.leaf_interval(node_id)[0])
        cache[node_id] = result
        return result

    def evaluate(self, node_id: str, memo: dict[str, frozenset[str]]):
        """(nominal, lo, hi, method, interval parents); all None for a non-numeric fact."""
        node = self.catalog.nodes[node_id]
        if isinstance(node, Fact) and not node.numeric:
            return None, None, None, "point", ()
        nominal = self.value(node_id, {}, {})
        parents = sorted(self.interval_leaves(node_id, memo))
        if not parents:
            return nominal, nominal, nominal, "point", ()
        bounds = [self.leaf_interval(p)[1:] for p in parents]
        values = [nominal]
        if len(parents) <= CORNER_LIMIT:
            method: Method = "corners"
            for corner in itertools.product(*bounds):
                values.append(self.value(node_id, dict(zip(parents, corner, strict=True)), {}))
        else:
            method = "monte_carlo"
            rng = np.random.default_rng(MC_SEED)
            lows = np.array([b[0] for b in bounds])
            highs = np.array([b[1] for b in bounds])
            for row in rng.uniform(lows, highs, size=(MC_SAMPLES, len(parents))):
                values.append(
                    self.value(node_id, dict(zip(parents, row.tolist(), strict=True)), {})
                )
        return nominal, min(values), max(values), method, tuple(parents)


def _ancestors(catalog: Catalog, roots: list[str]) -> set[str]:
    out: set[str] = set()
    stack = list(roots)
    while stack:
        node_id = stack.pop()
        if node_id in out:
            continue
        out.add(node_id)
        node = catalog.nodes[node_id]
        if isinstance(node, Derived):
            stack.extend(node.inputs)
    return out


def _check(graph: _Graph, check: Check, values: Mapping[str, tuple[float, float, float]]):
    catalog = graph.catalog
    a_nom, a_lo, a_hi = values[check.a]
    b_nom, b_lo, b_hi = values[check.b]
    gap_abs = a_nom - b_nom
    gap_rel = abs(gap_abs) / abs(b_nom) if b_nom != 0 else None
    tol_abs = check.rel_tol * abs(b_nom)
    b_node = catalog.nodes[check.b]
    unit = catalog.unit_of(check.a)
    if check.kind == "bound":
        if check.relation is not None:
            greater, label = check.relation == "ge", "required"
        else:
            assert isinstance(b_node, Fact)
            greater, label = b_node.bound == "min", b_node.bound
        ok = a_nom >= b_nom - tol_abs if greater else a_nom <= b_nom + tol_abs
        relation = "≥" if greater else "≤"
        detail = f"{with_unit(a_nom, unit)} {relation} {with_unit(b_nom, unit)} ({label})"
        detail += " holds" if ok else " fails"
    else:
        ok = abs(gap_abs) <= tol_abs
        rel_text = "n/a" if gap_rel is None else f"{100 * gap_rel:.3g}%"
        detail = (
            f"{with_unit(a_nom, unit)} vs {with_unit(b_nom, unit)}: gap {rel_text}, "
            f"tolerance {100 * check.rel_tol:.3g}%"
        )
    both_facts = isinstance(catalog.nodes[check.a], Fact) and isinstance(b_node, Fact)
    status: Status = "CONSISTENT" if ok else ("CONFLICT" if both_facts else "TENSION")
    overlap = (a_lo - tol_abs) <= (b_hi + tol_abs) and (b_lo - tol_abs) <= (a_hi + tol_abs)
    return CheckOutcome(
        id=check.id,
        kind=check.kind,
        a=check.a,
        b=check.b,
        unit=unit,
        a_value=a_nom,
        b_value=b_nom,
        gap_abs=gap_abs,
        gap_rel=gap_rel,
        rel_tol=check.rel_tol,
        status=status,
        interval_overlap=overlap,
        explanation=f"{detail} → {status}",
    )


def _scope(catalog: Catalog, product: str | None) -> tuple[list[str], list[Check], list[str]]:
    """(node ids to report, checks, hypothesis ids) for one file or the whole catalog."""
    if product is None:
        files = list(catalog.files.values())
    elif product in catalog.files:
        files = [catalog.files[product]]
    else:
        raise KeyError(f"no catalog file {product!r}")
    own = [i for f in files for i in f.node_ids()]
    checks = [c for f in files for c in f.check]
    roots = own + [x for c in checks for x in (c.a, c.b)]
    reported = sorted(_ancestors(catalog, roots), key=lambda i: (catalog.owner[i] != product, i))
    hypotheses = [h.id for f in files for h in f.hypothesis]
    return reported, checks, hypotheses


def _run(catalog: Catalog, pins: Mapping[str, tuple[float, str]], node_ids: list[str]):
    graph = _Graph(catalog, pins)
    memo: dict[str, frozenset[str]] = {}
    return graph, {i: graph.evaluate(i, memo) for i in node_ids}


def evaluate_graph(
    catalog: Catalog,
    product: str | None = None,
    overrides: Mapping[str, float] | None = None,
    hypotheses: tuple[str, ...] = (),
) -> EvaluatedGraph:
    """Evaluate one catalog file (with every ancestor it needs) or, with product None, all of it.

    overrides pin assumptions to values (what-if inputs). hypotheses pin the assumptions their
    `sets` name, at most one hypothesis per group; they take precedence over overrides. Raises
    KeyError for an unknown product, hypothesis or assumption and CatalogError for invalid input.
    """
    overrides = dict(overrides or {})
    node_ids, checks, file_hypotheses = _scope(catalog, product)
    pins: dict[str, tuple[float, str]] = {}
    for target, value in overrides.items():
        node = catalog.nodes.get(target)
        if not isinstance(node, Assumption):
            raise KeyError(f"override target {target!r} is not an assumption")
        if not math.isfinite(value):
            raise CatalogError(f"override {target} must be finite")
        pins[target] = (float(value), "override")
    groups: dict[str, str] = {}
    for h_id in hypotheses:
        h = catalog.hypotheses.get(h_id)
        if h is None:
            raise KeyError(f"unknown hypothesis {h_id!r}")
        if h.group and h.group in groups:
            raise CatalogError(f"{h_id} and {groups[h.group]} are alternatives (group {h.group})")
        if h.group:
            groups[h.group] = h_id
        pins.update({t: (v, h_id) for t, v in h.sets.items()})

    graph, values = _run(catalog, pins, node_ids)
    nodes = tuple(_node_result(catalog, graph, i, values[i]) for i in node_ids)
    simple = {i: (v[0], v[1], v[2]) for i, v in values.items() if v[0] is not None}
    outcomes = tuple(_check(graph, c, simple) for c in checks)

    support = [_support_row(catalog, "baseline", "", "No hypothesis applied.", outcomes)]
    for h_id in file_hypotheses:
        h = catalog.hypotheses[h_id]
        h_pins = {**pins, **{t: (v, h_id) for t, v in h.sets.items()}}
        h_graph, h_values = _run(catalog, h_pins, node_ids)
        h_simple = {i: (v[0], v[1], v[2]) for i, v in h_values.items() if v[0] is not None}
        h_out = tuple(_check(h_graph, c, h_simple) for c in checks)
        support.append(_support_row(catalog, h_id, h.group, h.statement, h_out))

    return EvaluatedGraph(
        scope=product or "all",
        hypotheses=tuple(hypotheses),
        overrides=overrides,
        nodes=nodes,
        checks=outcomes,
        conflicts=_conflicts(catalog, node_ids),
        support=tuple(support),
        tornado=tuple(
            _tornado(graph, i, simple[i][0]) for i in node_ids if _is_derived(catalog, i)
        ),
    )


def _is_derived(catalog: Catalog, node_id: str) -> bool:
    return isinstance(catalog.nodes[node_id], Derived)


def _node_result(catalog: Catalog, graph: _Graph, node_id: str, value) -> NodeResult:
    nominal, lo, hi, method, parents = value
    node = catalog.nodes[node_id]
    pinned_by = graph.pins.get(node_id, (None, None))[1]
    common = {
        "id": node_id,
        "unit": node.unit,
        "nominal": nominal,
        "lo": lo,
        "hi": hi,
        "method": method,
        "interval_parents": parents,
        "flagged": method == "monte_carlo",
        "pinned_by": pinned_by,
        "file": catalog.owner[node_id],
    }
    if isinstance(node, Derived):
        formula = FORMULAS[node.fn]
        args = tuple(graph.value(i, {}, {}) for i in node.inputs)
        units = tuple(catalog.unit_of(i) for i in node.inputs)
        derivation = f"{render(formula, args, units)} = {with_unit(nominal, node.unit)}"
        return NodeResult(
            kind="derived",
            label=node.note or node.id,
            source_class=SourceClass.INFERENCE,
            derivation=derivation,
            inputs=node.inputs,
            **common,
        )
    if isinstance(node, Assumption):
        pinned = f", pinned by {pinned_by}" if pinned_by else ""
        return NodeResult(
            kind="assumption",
            label=node.rationale,
            source_class=SourceClass.SYNTHETIC,
            derivation=(
                f"assumption {with_unit(nominal, node.unit)} (range {format_number(node.low)} "
                f"to {with_unit(node.high, node.unit)}{pinned})"
            ),
            inputs=(),
            **common,
        )
    assert isinstance(node, Fact)
    return NodeResult(
        kind="fact",
        label=node.quantity,
        source_class=node.source_class,
        derivation=f"{_fact_value_text(node)} ({node.cite})",
        inputs=(),
        verified=node.verified,
        cite=node.cite,
        quote=node.quote,
        bound=node.bound,
        **common,
    )


def _support_row(catalog, h_id, group, statement, outcomes) -> SupportRow:
    cells = {o.id: SupportCell(status=o.status, gap_rel=o.gap_rel) for o in outcomes}
    return SupportRow(
        hypothesis=h_id,
        group=group,
        statement=statement,
        cells=cells,
        agrees=tuple(o.id for o in outcomes if o.status == "CONSISTENT"),
        disagrees=tuple(o.id for o in outcomes if o.status != "CONSISTENT"),
    )


def _conflicts(catalog: Catalog, node_ids: list[str]) -> tuple[ConflictPair, ...]:
    in_scope = set(node_ids)
    pairs: set[tuple[str, str]] = set()
    for node_id in node_ids:
        node = catalog.nodes[node_id]
        if isinstance(node, Fact):
            for other in node.conflicts_with:
                pairs.add(tuple(sorted((node_id, other))))  # type: ignore[arg-type]
    out = []
    for a, b in sorted(pairs):
        fa, fb = catalog.nodes[a], catalog.nodes[b]
        assert isinstance(fa, Fact) and isinstance(fb, Fact)
        if a in in_scope or b in in_scope:
            out.append(
                ConflictPair(
                    a=a,
                    b=b,
                    quantity_a=fa.quantity,
                    quantity_b=fb.quantity,
                    quote_a=fa.quote,
                    quote_b=fb.quote,
                    cite_a=fa.cite,
                    cite_b=fb.cite,
                    value_a=_fact_value_text(fa),
                    value_b=_fact_value_text(fb),
                )
            )
    return tuple(out)


def _tornado(graph: _Graph, node_id: str, nominal: float) -> TornadoEntry:
    catalog = graph.catalog
    bars = []
    for leaf in sorted(_ancestors(catalog, [node_id])):
        node = catalog.nodes[leaf]
        if not isinstance(node, Assumption) or leaf in graph.pins or node.low == node.high:
            continue
        at_low = graph.value(node_id, {leaf: node.low}, {})
        at_high = graph.value(node_id, {leaf: node.high}, {})
        bars.append(
            TornadoBar(
                assumption=leaf,
                low=node.low,
                high=node.high,
                value_at_low=at_low,
                value_at_high=at_high,
                swing=abs(at_high - at_low),
            )
        )
    bars.sort(key=lambda b: (-b.swing, b.assumption))
    return TornadoEntry(node=node_id, nominal=nominal, bars=tuple(bars))
