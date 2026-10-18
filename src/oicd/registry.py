"""Constraint identifiers and numerical tolerances shared by the checks."""

from enum import StrEnum


class ConstraintId(StrEnum):
    ELECTRICAL_MATCH = "electrical_match"
    WAVELENGTH_CONTAINMENT = "wavelength_containment"
    OPTICAL_POWER_BUDGET = "optical_power_budget"
    BER = "ber"
    TDECQ = "tdecq"
    DISPERSION = "dispersion"
    REFLECTIONS_MPI = "reflections_mpi"
    THERMAL = "thermal"
    RELIABILITY = "reliability"


EVALUATED = frozenset(
    {
        ConstraintId.ELECTRICAL_MATCH,
        ConstraintId.WAVELENGTH_CONTAINMENT,
        ConstraintId.OPTICAL_POWER_BUDGET,
    }
)
NOT_EVALUATED = frozenset(ConstraintId) - EVALUATED

# Numerical tolerances, not physical parameters. Model card §3: PASS iff M_net >= -epsilon,
# so float sums that land a hair below an exact boundary (T04) still pass.
EPSILON_DB = 1e-9
# Same idea for wavelength interval containment at an exact edge.
EPSILON_NM = 1e-9
