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
