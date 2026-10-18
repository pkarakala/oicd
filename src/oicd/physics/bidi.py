"""BiDi reflection crosstalk (model card §12.4, bhatt2001_bidixtalk).

T = 10^(−IL/10), R = 10^(−(RL + I)/10), Π_xtalk = 10·log10(T/(T − R)), invalid if R ≥ T.

I = 0 is the source's single-wavelength formula. I > 0 (diplexer isolation of the receiver from
the local transmitter's wavelength) is OICD's two-wavelength extension, labeled INFERENCE.
"""

import math

from pydantic import BaseModel, ConfigDict

from oicd.provenance import SourceClass

_FROZEN = ConfigDict(frozen=True, extra="forbid")

# Source rule (bhatt2001_bidixtalk): keep the return loss at least 5 dB above the channel IL.
RETURN_LOSS_RULE_MARGIN_DB = 5.0


class ReflectionCrosstalk(BaseModel):
    model_config = _FROZEN

    t_linear: float
    r_linear: float
    penalty_db: float
    rule_margin_db: float  # RL − (IL + 5 dB); ≥ 0 meets the source's thumb rule
    meets_return_loss_rule: bool
    source_class: SourceClass
    method: str


def _finite(value: float, name: str, *, minimum: float = 0.0) -> float:
    if not math.isfinite(value) or value < minimum:
        raise ValueError(f"{name} must be finite and >= {minimum}, got {value!r}")
    return float(value)


def reflection_crosstalk_db(
    il_db: float, rl_db: float, isolation_db: float = 0.0
) -> ReflectionCrosstalk:
    """Crosstalk penalty from the local transmitter's reflection reaching the local receiver."""
    il = _finite(il_db, "il_db")
    rl = _finite(rl_db, "rl_db")
    isolation = _finite(isolation_db, "isolation_db")
    t = 10.0 ** (-il / 10.0)
    r = 10.0 ** (-(rl + isolation) / 10.0)
    if r >= t:
        raise ValueError(
            f"reflection ({rl + isolation} dB below launch) is not below the signal "
            f"({il} dB below launch): the crosstalk penalty is unbounded"
        )
    margin = rl - (il + RETURN_LOSS_RULE_MARGIN_DB)
    extension = isolation > 0.0
    return ReflectionCrosstalk(
        t_linear=t,
        r_linear=r,
        penalty_db=10.0 * math.log10(t / (t - r)),
        rule_margin_db=margin,
        meets_return_loss_rule=margin >= 0.0,
        source_class=SourceClass.INFERENCE if extension else SourceClass.PROPOSED_STANDARD,
        method=(
            "bhatt2001_bidixtalk with diplexer isolation added to the return loss (INFERENCE)"
            if extension
            else "bhatt2001_bidixtalk single-wavelength formula"
        ),
    )
