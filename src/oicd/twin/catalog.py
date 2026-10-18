"""Twin catalog (model card §14): public facts, assumptions, derived nodes, checks and hypotheses
per product, loaded from catalog/products/*.toml with tomllib, and part geometry from
catalog/geometry/*.toml.

Node ids are global across files, so a product can derive from another file's facts (the L20
twin uses the draft IEEE 802.3dj wavelength range, for example). Validation covers unique ids,
every citation key in references.bib, inputs that resolve to numeric nodes, formula arity and
units, no cycles, checks between nodes of the same unit, and hypotheses that pin assumptions
inside their stated range.
"""

import re
import tomllib
from collections.abc import Iterable
from functools import cached_property
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from oicd.provenance import SourceClass, load_citation_keys
from oicd.twin.formulas import FORMULAS, resolve_out_unit

# src/oicd/twin/catalog.py -> repo root.
CATALOG_DIR = Path(__file__).resolve().parents[3] / "catalog"
PRODUCTS_DIR = CATALOG_DIR / "products"
GEOMETRY_DIR = CATALOG_DIR / "geometry"
UNOPENED_PATH = CATALOG_DIR / "unopened_sources.toml"

# An unverified fact taken from the brief's Appendix A with no source that could confirm it.
APPENDIX_KEY = "appendix_a"

_FROZEN = ConfigDict(frozen=True, extra="forbid")
_ID = r"^[a-z0-9_]+(\.[a-z0-9_]+)+$"
_HYPOTHESIS_ID = r"^H_[A-Za-z0-9_]+$"

# Facts come from sources; SYNTHETIC and INFERENCE values are assumptions and derived nodes.
FACT_CLASSES = frozenset(
    {
        SourceClass.PUBLISHED_SPEC,
        SourceClass.PROPOSED_STANDARD,
        SourceClass.VENDOR_CLAIM,
        SourceClass.PEER_REVIEWED,
        SourceClass.THIRD_PARTY,
    }
)

Bound = Literal["min", "max", "approx", "exact"]


class CatalogError(ValueError):
    """A catalog file or the catalog as a whole is invalid."""


class ProductInfo(BaseModel):
    model_config = _FROZEN

    name: str
    family: str
    status: str
    summary: str
    kind: Literal["product", "reference", "system"] = "product"


class Fact(BaseModel):
    """A public statement with its exact quote. value, or lo and hi for a range, or neither for a
    non-numeric statement (e.g. a modulation format)."""

    model_config = _FROZEN

    id: str = Field(pattern=_ID)
    quantity: str
    value: float | None = None
    lo: float | None = None
    hi: float | None = None
    bound: Bound = "exact"
    unit: str
    quote: str
    cite: str
    source_class: SourceClass
    verified: bool
    conflicts_with: tuple[str, ...] = ()
    location: str = ""
    note: str = ""

    @model_validator(mode="after")
    def _check(self) -> Self:
        if self.source_class not in FACT_CLASSES:
            raise ValueError(f"{self.id}: a fact's class must be cited, got {self.source_class}")
        if self.value is not None and (self.lo is not None or self.hi is not None):
            raise ValueError(f"{self.id}: give value or lo and hi, not both")
        if (self.lo is None) != (self.hi is None):
            raise ValueError(f"{self.id}: a range needs both lo and hi")
        if self.lo is not None and self.hi is not None and not self.lo <= self.hi:
            raise ValueError(f"{self.id}: lo must be <= hi")
        if not self.quote.strip():
            raise ValueError(f"{self.id}: quote must not be blank")
        if not self.verified and not self.note.strip():
            raise ValueError(f"{self.id}: an unverified fact needs a note saying why")
        return self

    @property
    def numeric(self) -> bool:
        return self.value is not None or self.lo is not None

    @property
    def nominal(self) -> float:
        """The value, or the middle of the range."""
        if self.value is not None:
            return self.value
        if self.lo is None or self.hi is None:
            raise CatalogError(f"{self.id} is not numeric")
        return (self.lo + self.hi) / 2.0


class Assumption(BaseModel):
    """A SYNTHETIC value with its plausible range and why."""

    model_config = _FROZEN

    id: str = Field(pattern=_ID)
    nominal: float
    low: float
    high: float
    unit: str
    rationale: str

    @model_validator(mode="after")
    def _check(self) -> Self:
        if not self.low <= self.nominal <= self.high:
            raise ValueError(f"{self.id}: need low <= nominal <= high")
        if not self.rationale.strip():
            raise ValueError(f"{self.id}: rationale must not be blank")
        return self


class Derived(BaseModel):
    """An INFERENCE node: a registered formula of other nodes."""

    model_config = _FROZEN

    id: str = Field(pattern=_ID)
    fn: str
    inputs: tuple[str, ...]
    unit: str
    note: str = ""

    @field_validator("fn")
    @classmethod
    def _known_formula(cls, fn: str) -> str:
        if fn not in FORMULAS:
            raise ValueError(f"unknown formula {fn!r}")
        return fn


class Check(BaseModel):
    """consistent: |a − b| ≤ rel_tol·|b|. bound: a ≥ b or a ≤ b, from b's min or max bound when b
    is such a fact, otherwise from `relation` ("ge" or "le")."""

    model_config = _FROZEN

    id: str = Field(pattern=_ID)
    kind: Literal["consistent", "bound"]
    a: str
    b: str
    rel_tol: float = Field(ge=0.0)
    relation: Literal["le", "ge"] | None = None
    note: str = ""

    @model_validator(mode="after")
    def _relation_only_for_bounds(self) -> Self:
        if self.relation is not None and self.kind != "bound":
            raise ValueError(f"{self.id}: relation applies to bound checks only")
        return self


class Hypothesis(BaseModel):
    """A named reading of an ambiguous claim: pins assumptions to values (model card §14)."""

    model_config = _FROZEN

    id: str = Field(pattern=_HYPOTHESIS_ID)
    statement: str
    sets: dict[str, float]
    group: str = ""
    note: str = ""


class CatalogFile(BaseModel):
    model_config = _FROZEN

    product: ProductInfo
    fact: tuple[Fact, ...] = ()
    assumption: tuple[Assumption, ...] = ()
    derived: tuple[Derived, ...] = ()
    check: tuple[Check, ...] = ()
    hypothesis: tuple[Hypothesis, ...] = ()

    def node_ids(self) -> Iterable[str]:
        yield from (f.id for f in self.fact)
        yield from (a.id for a in self.assumption)
        yield from (d.id for d in self.derived)


Node = Fact | Assumption | Derived


class Catalog(BaseModel):
    """All catalog files, validated together. Pass context={"citation_keys": ...} to
    model_validate to check citations against another set than references.bib."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    files: dict[str, CatalogFile]

    @cached_property
    def nodes(self) -> dict[str, Node]:
        return {n.id: n for f in self.files.values() for n in (*f.fact, *f.assumption, *f.derived)}

    @cached_property
    def checks(self) -> dict[str, Check]:
        return {c.id: c for f in self.files.values() for c in f.check}

    @cached_property
    def hypotheses(self) -> dict[str, Hypothesis]:
        return {h.id: h for f in self.files.values() for h in f.hypothesis}

    @cached_property
    def owner(self) -> dict[str, str]:
        """File stem that defines each node, check and hypothesis id."""
        out: dict[str, str] = {}
        for stem, f in self.files.items():
            for item in (*f.fact, *f.assumption, *f.derived, *f.check, *f.hypothesis):
                out[item.id] = stem
        return out

    def unit_of(self, node_id: str) -> str:
        return self.nodes[node_id].unit

    @model_validator(mode="after")
    def _validate(self, info: ValidationInfo) -> Self:
        errors: list[str] = []
        seen: dict[str, str] = {}
        for stem, f in self.files.items():
            for item in (*f.fact, *f.assumption, *f.derived, *f.check, *f.hypothesis):
                if item.id in seen:
                    errors.append(f"duplicate id {item.id!r} in {stem} and {seen[item.id]}")
                seen[item.id] = stem
        context = info.context or {}
        keys = context.get("citation_keys")
        if keys is None:
            keys = load_citation_keys()
        unopened = context.get("unopened_keys")
        if unopened is None:
            unopened = load_unopened_keys()
        nodes = {n.id: n for f in self.files.values() for n in (*f.fact, *f.assumption, *f.derived)}

        def numeric(node_id: str, where: str) -> bool:
            node = nodes.get(node_id)
            if node is None:
                errors.append(f"{where}: unknown node {node_id!r}")
                return False
            if isinstance(node, Fact) and not node.numeric:
                errors.append(f"{where}: fact {node_id!r} has no number")
                return False
            return True

        for f in self.files.values():
            for fact in f.fact:
                # Verified facts cite an opened source; an unverified fact may also cite a source
                # that could not be opened (unopened_sources.toml) or the brief's Appendix A.
                allowed = keys if fact.verified else (keys | unopened | {APPENDIX_KEY})
                if fact.cite not in allowed:
                    where = "references.bib" if fact.verified else "references.bib or unopened"
                    errors.append(f"{fact.id}: cite {fact.cite!r} not in {where}")
                for other in fact.conflicts_with:
                    if not isinstance(nodes.get(other), Fact):
                        errors.append(f"{fact.id}: conflicts_with unknown fact {other!r}")
            for d in f.derived:
                if all(numeric(i, d.id) for i in d.inputs):
                    try:
                        unit = resolve_out_unit(
                            FORMULAS[d.fn], tuple(nodes[i].unit for i in d.inputs)
                        )
                    except ValueError as exc:
                        errors.append(f"{d.id}: {exc}")
                    else:
                        if unit != d.unit:
                            errors.append(f"{d.id}: {d.fn} gives {unit}, the node says {d.unit}")
            for c in f.check:
                if numeric(c.a, c.id) and numeric(c.b, c.id):
                    if nodes[c.a].unit != nodes[c.b].unit:
                        errors.append(f"{c.id}: compares {nodes[c.a].unit} with {nodes[c.b].unit}")
                    b = nodes[c.b]
                    bounded = isinstance(b, Fact) and b.bound in ("min", "max")
                    if c.kind == "bound" and not bounded and c.relation is None:
                        errors.append(
                            f"{c.id}: a bound check needs b to be a min or max fact or a relation"
                        )
            for h in f.hypothesis:
                for target, value in h.sets.items():
                    node = nodes.get(target)
                    if not isinstance(node, Assumption):
                        errors.append(f"{h.id}: sets {target!r}, which is not an assumption")
                    elif not node.low <= value <= node.high:
                        errors.append(
                            f"{h.id}: sets {target} = {value}, outside [{node.low}, {node.high}]"
                        )
        errors += _cycles({d.id: d.inputs for f in self.files.values() for d in f.derived})
        if errors:
            raise CatalogError("invalid catalog:\n  " + "\n  ".join(errors))
        return self


def _cycles(edges: dict[str, tuple[str, ...]]) -> list[str]:
    """Derived nodes that depend on themselves (iterative depth-first search)."""
    state: dict[str, int] = {}  # 1 = on the stack, 2 = done
    errors: list[str] = []
    for start in sorted(edges):
        if state.get(start):
            continue
        stack: list[tuple[str, int]] = [(start, 0)]
        state[start] = 1
        while stack:
            node, i = stack[-1]
            children = edges.get(node, ())
            if i < len(children):
                stack[-1] = (node, i + 1)
                child = children[i]
                if state.get(child) == 1:
                    errors.append(f"cycle through {child!r}")
                elif not state.get(child) and child in edges:
                    state[child] = 1
                    stack.append((child, 0))
            else:
                state[node] = 2
                stack.pop()
    return errors


class UnopenedSource(BaseModel):
    """A source the brief names that could not be opened in this run (never in references.bib)."""

    model_config = _FROZEN

    key: str
    url: str
    tried: tuple[str, ...]
    result: str
    date: str


def load_unopened_sources(path: Path = UNOPENED_PATH) -> tuple[UnopenedSource, ...]:
    if not path.is_file():
        return ()
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    return tuple(UnopenedSource.model_validate(s) for s in data.get("source", []))


def load_unopened_keys(path: Path = UNOPENED_PATH) -> frozenset[str]:
    return frozenset(s.key for s in load_unopened_sources(path))


def load_catalog_file(path: Path) -> CatalogFile:
    with path.open("rb") as handle:
        return CatalogFile.model_validate(tomllib.load(handle))


def load_catalog(
    directory: Path = PRODUCTS_DIR, citation_keys: frozenset[str] | None = None
) -> Catalog:
    """Every *.toml in the directory, keyed by file stem, validated as one catalog. Citations
    are checked against references.bib unless citation_keys is given."""
    files = {p.stem: load_catalog_file(p) for p in sorted(directory.glob("*.toml"))}
    context = None if citation_keys is None else {"citation_keys": citation_keys}
    return Catalog.model_validate({"files": files}, context=context)


# ---- Geometry ------------------------------------------------------------------------------

DimsClass = Literal["PUBLISHED", "VENDOR", "INFERENCE", "SCHEMATIC"]


class Part(BaseModel):
    """One part of a scene, in the scene's unit. size is the bounding box (x, y, z)."""

    model_config = _FROZEN

    id: str = Field(pattern=_ID)
    name: str
    assembly: str = ""
    shape: Literal["box", "cylinder", "sphere", "tube", "ring", "array"] = "box"
    size: tuple[float, float, float]
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)
    material: str
    dims_class: DimsClass
    dims_source: str  # a fact or derived id, or the reason a SCHEMATIC size was chosen
    function: str = ""
    explode: tuple[float, float, float] = (0.0, 0.0, 0.0)
    count: int = Field(default=1, ge=1)
    pitch: tuple[float, float, float] = (0.0, 0.0, 0.0)
    grid: tuple[int, int, int] = (1, 1, 1)

    @model_validator(mode="after")
    def _check(self) -> Self:
        if any(s <= 0 for s in self.size):
            raise ValueError(f"{self.id}: sizes must be positive")
        if self.grid[0] * self.grid[1] * self.grid[2] != self.count:
            raise ValueError(f"{self.id}: grid {self.grid} does not hold count {self.count}")
        if not self.dims_source.strip():
            raise ValueError(f"{self.id}: dims_source must say where the size comes from")
        return self


class SceneInfo(BaseModel):
    model_config = _FROZEN

    id: str
    name: str
    unit: Literal["m", "mm", "um", "nm"]
    summary: str
    level: Literal["rack", "tray", "package", "pic", "device"]


class GeometryScene(BaseModel):
    model_config = _FROZEN

    scene: SceneInfo
    part: tuple[Part, ...]

    @model_validator(mode="after")
    def _unique(self) -> Self:
        ids = [p.id for p in self.part]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{self.scene.id}: duplicate part ids")
        return self


_SCENE_RE = re.compile(r"^[a-z0-9_]+$")


def geometry_path(scene: str, directory: Path = GEOMETRY_DIR) -> Path:
    """catalog/geometry/<scene>.toml; names are [a-z0-9_] only. FileNotFoundError otherwise."""
    if not _SCENE_RE.match(scene):
        raise FileNotFoundError(f"invalid scene name {scene!r}")
    path = directory / f"{scene}.toml"
    if not path.is_file():
        raise FileNotFoundError(f"no scene named {scene!r}")
    return path


def load_geometry(scene: str, directory: Path = GEOMETRY_DIR) -> GeometryScene:
    with geometry_path(scene, directory).open("rb") as handle:
        return GeometryScene.model_validate(tomllib.load(handle))


def validate_geometry_sources(scene: GeometryScene, catalog: Catalog) -> list[str]:
    """Parts whose dims_class claims a source but whose dims_source is not a catalog node."""
    return [
        f"{p.id}: dims_source {p.dims_source!r} is not a catalog node"
        for p in scene.part
        if p.dims_class != "SCHEMATIC" and p.dims_source not in catalog.nodes
    ]
