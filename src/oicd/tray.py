"""Multi-lane tray (model card §9): a tray of N lanes is only as good as its worst lane.

M_tray = min_k M_net,k; EXCLUDED iff any lane is EXCLUDED; the deciding lane is the excluded
lane with the smallest margin if any lane is excluded, otherwise the lane with the smallest
margin, ties to the lowest index. Lanes are indexed from 0 in request order.
"""

from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel, ConfigDict

from oicd.checks import Status
from oicd.registry import ConstraintId
from oicd.report import FeasibilityReport, evaluate
from oicd.schema import Link

_FROZEN = ConfigDict(frozen=True, extra="forbid")

MAX_LANES = 1024

Verdict = Literal["NOT_EXCLUDED", "EXCLUDED"]


class LaneSummary(BaseModel):
    model_config = _FROZEN

    index: int
    link_name: str
    verdict: Verdict
    margin_db: float
    failed: tuple[ConstraintId, ...]


class TrayReport(BaseModel):
    model_config = _FROZEN

    tray_name: str
    lane_count: int
    verdict: Verdict
    margin_db: float
    deciding_lane: int
    excluded_lanes: tuple[int, ...]
    lanes: tuple[LaneSummary, ...]
    deciding_report: FeasibilityReport


def _summary(index: int, report: FeasibilityReport) -> LaneSummary:
    return LaneSummary(
        index=index,
        link_name=report.link_name,
        verdict=report.verdict,
        margin_db=report.margin_db,
        failed=tuple(r.constraint for r in report.results if r.status is Status.FAIL),
    )


def evaluate_tray(lanes: Sequence[Link], name: str = "tray") -> TrayReport:
    """Evaluate every lane and combine them by §9. Raises ValueError for 0 or > 1024 lanes."""
    if not 1 <= len(lanes) <= MAX_LANES:
        raise ValueError(f"a tray needs 1 to {MAX_LANES} lanes, got {len(lanes)}")
    reports = [evaluate(lane) for lane in lanes]
    summaries = tuple(_summary(i, r) for i, r in enumerate(reports))
    excluded = tuple(s.index for s in summaries if s.verdict == "EXCLUDED")
    candidates = [summaries[i] for i in excluded] if excluded else list(summaries)
    # min() keeps the first of equal keys, so ties go to the lowest index.
    deciding = min(candidates, key=lambda s: s.margin_db)
    return TrayReport(
        tray_name=name,
        lane_count=len(summaries),
        verdict="EXCLUDED" if excluded else "NOT_EXCLUDED",
        margin_db=min(s.margin_db for s in summaries),
        deciding_lane=deciding.index,
        excluded_lanes=excluded,
        lanes=summaries,
        deciding_report=reports[deciding.index],
    )
