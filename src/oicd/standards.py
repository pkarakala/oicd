"""Draft IEEE P802.3dj values (model card §12). PROPOSED_STANDARD: draft D3.x, not approved.

Table 180-12, maximum channel insertion loss versus the number of discrete reflectances, as
proposed in johnson2025_3dj_mpidgd and unchanged in dawe2026_3dj_er199.
"""

from oicd.provenance import Provenance, Quantity, SourceClass
from oicd.units import DB

TABLE_180_12_PROVENANCE = Provenance(
    source_class=SourceClass.PROPOSED_STANDARD,
    citation_key="johnson2025_3dj_mpidgd",
    rationale="Draft IEEE P802.3dj Table 180-12, maximum channel insertion loss versus number "
    "of discrete reflectances (draft D3.x, not an approved standard).",
)

# Rows: reflectances in (-45, -35] dB, 0 to 6. Columns: reflectances in (-55, -45] dB, 0 to 8.
# None: the combination does not provide a supported maximum channel insertion loss.
TABLE_180_12_DB: tuple[tuple[float | None, ...], ...] = (
    (3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 2.9, 2.9, 2.9),
    (3.0, 3.0, 3.0, 2.9, 2.9, 2.9, 2.9, 2.8, 2.8),
    (2.9, 2.9, 2.9, 2.8, 2.8, 2.8, 2.7, 2.7, 2.7),
    (2.8, 2.8, 2.7, 2.7, 2.7, 2.6, 2.6, 2.6, 2.6),
    (2.7, 2.6, 2.6, 2.6, 2.5, 2.5, 2.5, 2.5, None),
    (2.5, 2.5, 2.5, None, None, None, None, None, None),
    (None, None, None, None, None, None, None, None, None),
)


def max_channel_il(n_refl_45_35: int, n_refl_55_45: int) -> Quantity[DB] | None:
    """Maximum channel insertion loss for the given reflectance counts, or None if the draft does
    not support the combination (including counts beyond the table). Negative counts raise."""
    for name, count in (("n_refl_45_35", n_refl_45_35), ("n_refl_55_45", n_refl_55_45)):
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError(f"{name} must be an integer >= 0, got {count!r}")
    if n_refl_45_35 >= len(TABLE_180_12_DB) or n_refl_55_45 >= len(TABLE_180_12_DB[0]):
        return None
    value = TABLE_180_12_DB[n_refl_45_35][n_refl_55_45]
    if value is None:
        return None
    return Quantity(value=DB(value), provenance=TABLE_180_12_PROVENANCE)
