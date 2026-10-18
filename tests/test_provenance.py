"""Tests for oicd.provenance."""

import pytest
from pydantic import ValidationError

from oicd.provenance import (
    Provenance,
    Quantity,
    SourceClass,
    load_citation_keys,
    parse_bib_keys,
)
from oicd.units import DB

KNOWN_KEY = "lightmatter_guide_2026"

SAMPLE_BIB = """
% a comment line mentioning @misc{not_a_key, ...}
@misc{alpha_2026,
  title = {Alpha},
}
@TechReport{ beta-2025 ,
  title = {Beta},
}
@comment{ignored_comment, text}
@string{ignored_string = "x"}
"""


def test_parse_bib_keys_on_sample():
    assert parse_bib_keys(SAMPLE_BIB) == frozenset({"alpha_2026", "beta-2025"})


def test_load_citation_keys_reads_repo_bib():
    keys = load_citation_keys()
    assert KNOWN_KEY in keys
    assert "ocp_osp_vision_2026" in keys


def test_vendor_claim_with_known_key_is_accepted():
    p = Provenance(
        source_class=SourceClass.VENDOR_CLAIM,
        citation_key=KNOWN_KEY,
        rationale="16 wavelengths per fiber, vendor press release.",
    )
    assert p.citation_key == KNOWN_KEY


@pytest.mark.parametrize("source_class", [SourceClass.SYNTHETIC, SourceClass.INFERENCE])
def test_synthetic_and_inference_need_no_key(source_class):
    p = Provenance(source_class=source_class, rationale="Placeholder for a test.")
    assert p.citation_key is None


def test_unknown_citation_key_is_rejected():
    with pytest.raises(ValidationError, match="not_a_real_key_2099"):
        Provenance(
            source_class=SourceClass.PUBLISHED_SPEC,
            citation_key="not_a_real_key_2099",
            rationale="Does not exist.",
        )


def test_unknown_key_rejected_even_for_synthetic():
    with pytest.raises(ValidationError):
        Provenance(
            source_class=SourceClass.SYNTHETIC,
            citation_key="not_a_real_key_2099",
            rationale="Synthetic but cites a missing source.",
        )


@pytest.mark.parametrize(
    "source_class",
    [
        SourceClass.VENDOR_CLAIM,
        SourceClass.PUBLISHED_SPEC,
        SourceClass.PROPOSED_STANDARD,
    ],
)
def test_cited_classes_require_a_key(source_class):
    with pytest.raises(ValidationError, match="citation_key"):
        Provenance(source_class=source_class, rationale="Missing key.")


@pytest.mark.parametrize("rationale", ["", "   "])
def test_blank_rationale_is_rejected(rationale):
    with pytest.raises(ValidationError, match="rationale"):
        Provenance(source_class=SourceClass.SYNTHETIC, rationale=rationale)


def test_citation_keys_can_be_supplied_via_context():
    p = Provenance.model_validate(
        {
            "source_class": "vendor_claim",
            "citation_key": "only_in_context",
            "rationale": "Context-supplied key set.",
        },
        context={"citation_keys": frozenset({"only_in_context"})},
    )
    assert p.citation_key == "only_in_context"


def test_provenance_is_frozen():
    p = Provenance(source_class=SourceClass.SYNTHETIC, rationale="Frozen check.")
    with pytest.raises(ValidationError):
        p.rationale = "changed"


def test_quantity_holds_value_and_provenance():
    prov = Provenance(
        source_class=SourceClass.SYNTHETIC,
        rationale="Typical connector loss placeholder for tests.",
    )
    q = Quantity[DB](value=DB(0.5), provenance=prov)
    assert q.value == DB(0.5)
    assert q.provenance.source_class is SourceClass.SYNTHETIC
    with pytest.raises(ValidationError):
        q.value = DB(1.0)
