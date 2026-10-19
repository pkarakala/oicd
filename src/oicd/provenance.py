"""Provenance of physical parameters and citation-key validation."""

from __future__ import annotations

import functools
import re
from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, ValidationInfo, model_validator

# src/oicd/provenance.py -> repo root.
DEFAULT_BIB_PATH = Path(__file__).resolve().parents[2] / "references.bib"

_BIB_KEY_RE = re.compile(r"^\s*@(\w+)\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)
_NON_ENTRY_TYPES = frozenset({"comment", "string", "preamble"})


class SourceClass(StrEnum):
    PUBLISHED_SPEC = "published_spec"
    PROPOSED_STANDARD = "proposed_standard"
    VENDOR_CLAIM = "vendor_claim"
    PEER_REVIEWED = "peer_reviewed"  # peer-reviewed paper, including vendor-authored ones
    THIRD_PARTY = "third_party"  # analysts and press reporting on someone else's product
    SYNTHETIC = "synthetic"
    INFERENCE = "inference"


_KEY_OPTIONAL = frozenset({SourceClass.SYNTHETIC, SourceClass.INFERENCE})


def parse_bib_keys(text: str) -> frozenset[str]:
    """Extract entry keys from BibTeX source text."""
    return frozenset(
        key
        for entry_type, key in _BIB_KEY_RE.findall(text)
        if entry_type.lower() not in _NON_ENTRY_TYPES
    )


@functools.cache
def load_citation_keys(path: Path = DEFAULT_BIB_PATH) -> frozenset[str]:
    return parse_bib_keys(path.read_text(encoding="utf-8"))


class BibEntry(BaseModel):
    """One references.bib entry, for showing a citation with its source link."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: str
    entry_type: str
    title: str
    year: str = ""
    url: str = ""
    note: str = ""


def _braced(text: str, start: int) -> tuple[str, int]:
    """The text inside the brace group opening at text[start], and the index after it."""
    depth, i = 0, start
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : i], i + 1
        i += 1
    raise ValueError("unbalanced braces in references.bib")


_FIELD_RE = re.compile(r"\s*,?\s*(\w+)\s*=\s*")


def parse_bib_entries(text: str) -> tuple[BibEntry, ...]:
    """Entries with their title, year, url and note; braces inside values are dropped."""
    out = []
    for match in _BIB_KEY_RE.finditer(text):
        entry_type, key = match.group(1).lower(), match.group(2)
        if entry_type in _NON_ENTRY_TYPES:
            continue
        body, _ = _braced(text, text.index("{", match.start()))
        fields: dict[str, str] = {}
        i = body.index(",") + 1
        while (field := _FIELD_RE.match(body, i)) is not None and field.end() < len(body):
            name, j = field.group(1).lower(), field.end()
            if body[j] == "{":
                value, i = _braced(body, j)
            else:
                end = body.find(",", j)
                value, i = (body[j:] if end < 0 else body[j:end]), (len(body) if end < 0 else end)
            fields[name] = " ".join(value.replace("{", "").replace("}", "").split())
        out.append(
            BibEntry(
                key=key,
                entry_type=entry_type,
                title=fields.get("title", ""),
                year=fields.get("year", ""),
                url=fields.get("url", ""),
                note=fields.get("note", ""),
            )
        )
    return tuple(out)


class Provenance(BaseModel):
    """Where a value comes from.

    citation_key is required unless the source class is SYNTHETIC or INFERENCE,
    and any key given must exist in references.bib. Pass
    context={"citation_keys": ...} to model_validate to check against another set.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_class: SourceClass
    citation_key: str | None = None
    rationale: str

    @model_validator(mode="after")
    def _check_citation(self, info: ValidationInfo) -> Self:
        if not self.rationale.strip():
            raise ValueError("rationale must not be blank")
        if self.citation_key is None:
            if self.source_class not in _KEY_OPTIONAL:
                raise ValueError(f"citation_key is required for {self.source_class.value}")
            return self
        context = info.context or {}
        keys = context.get("citation_keys")
        if keys is None:
            keys = load_citation_keys()
        if self.citation_key not in keys:
            raise ValueError(f"citation_key {self.citation_key!r} not found in references.bib")
        return self


class Quantity[T](BaseModel):
    """A value together with its provenance."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: T
    provenance: Provenance
