"""Scale-up pod example (model card §14.8): fibers, fiber length and connectors of a BiDi pod
against the public claims (lm_pr_cpx, lm_hoti26). Pure functions; INFERENCE throughout."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

_FROZEN = ConfigDict(frozen=True, extra="forbid")

METERS_PER_MILE = 1609.344  # international mile, exact by definition


class PodSpec(BaseModel):
    model_config = _FROZEN

    xpus: int = Field(ge=1)
    bw_per_xpu_tbps: float = Field(gt=0)  # per direction
    lane_gbps: float = Field(gt=0)
    ferrule_fibers: int = Field(ge=1)  # SYNTHETIC: 16 (PRIZM TMT starts at 16)
    claimed_fibers_before: float | None = None
    claimed_fiber_saved_miles: tuple[float, ...] = ()
    claimed_connectors_saved: tuple[float, ...] = ()


class PodResult(BaseModel):
    model_config = _FROZEN

    source_class: Literal["inference"] = "inference"
    lanes_per_xpu: float
    duplex_fibers: float
    bidi_fibers: float
    fibers_saved: float
    gap_to_claimed_fibers: float | None  # (duplex − claim)/claim
    mean_length_m: tuple[float, ...]  # per claimed mileage, over the fibers saved
    connectors_per_mating_plane: float
    connector_ends_per_path: tuple[float, ...]  # claimed connectors saved / connectors per plane
    mated_pairs_per_path: tuple[float, ...]


def evaluate_pod(spec: PodSpec) -> PodResult:
    lanes = spec.bw_per_xpu_tbps * 1000.0 / spec.lane_gbps
    duplex = spec.xpus * lanes * 2.0
    bidi = spec.xpus * lanes
    saved = duplex - bidi
    per_plane = saved / spec.ferrule_fibers
    ends = tuple(c / per_plane for c in spec.claimed_connectors_saved)
    return PodResult(
        lanes_per_xpu=lanes,
        duplex_fibers=duplex,
        bidi_fibers=bidi,
        fibers_saved=saved,
        gap_to_claimed_fibers=None
        if spec.claimed_fibers_before is None
        else (duplex - spec.claimed_fibers_before) / spec.claimed_fibers_before,
        mean_length_m=tuple(m * METERS_PER_MILE / saved for m in spec.claimed_fiber_saved_miles),
        connectors_per_mating_plane=per_plane,
        connector_ends_per_path=ends,
        mated_pairs_per_path=tuple(e / 2.0 for e in ends),
    )
