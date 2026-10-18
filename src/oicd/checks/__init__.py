"""Constraint checks. Each check is a pure function Link -> CheckResult.

PASS means "not excluded by the modeled constraint", never "the link works".
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from oicd.registry import ConstraintId


class Status(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    NOT_EVALUATED = "not_evaluated"


class CheckResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    constraint: ConstraintId
    status: Status
    evidence: dict[str, float | str]
    message: str
