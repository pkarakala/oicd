"""Numeric input paths of a Link, as the report's InputRecord.path names them.

get_input reads a value; set_input returns a new, fully re-validated Link with one value
changed and relabeled SYNTHETIC (an edited value no longer matches its source).
Invalid physics raises ValueError exactly as constructing the Link would.
"""

import re
from typing import Any, Literal

from oicd.provenance import Provenance, SourceClass
from oicd.schema import Link

Unit = Literal["dB", "dBm OMA", "dBm AVERAGE", "nm", "count"]

EDITED = Provenance(
    source_class=SourceClass.SYNTHETIC,
    rationale="Set by an edit of the input (what-if value, not from a source).",
)

_INDEXED = re.compile(r"^(channel|penalties)\[(\d+)\]\.(loss_max|value)$")

# path -> (JSON keys from the Link down to the number, unit). Indexed paths are handled apart.
_FIXED: dict[str, tuple[tuple[str, ...], Unit]] = {
    "reserve": (("reserve", "value", "value"), "dB"),
    "tx.launch_oma_min": (("tx", "launch_oma_min", "value", "power_dbm", "value"), "dBm OMA"),
    "rx.sensitivity_oma_max": (
        ("rx", "sensitivity_oma_max", "value", "power_dbm", "value"),
        "dBm OMA",
    ),
    "tx.center_wavelength_nm": (("tx", "center_wavelength_nm", "value"), "nm"),
    "tx.wavelength_tolerance_nm": (("tx", "wavelength_tolerance_nm", "value"), "nm"),
    "rx.passband_min_nm": (("rx", "passband_min_nm", "value"), "nm"),
    "rx.passband_max_nm": (("rx", "passband_max_nm", "value"), "nm"),
    "tx.upstream.laser_power_avg": (
        ("tx", "upstream", "laser_power_avg", "value", "power_dbm", "value"),
        "dBm AVERAGE",
    ),
    "tx.upstream.split_n": (("tx", "upstream", "split_n", "value"), "count"),
    **{
        f"tx.upstream.{field}": (("tx", "upstream", field, "value", "value"), "dB")
        for field in (
            "laser_fiber_loss",
            "coupling_loss",
            "excess_loss",
            "modulator_il",
            "output_coupler_loss",
            "extinction_ratio",
        )
    },
}


def _keys(link: Link, path: str) -> tuple[tuple[str | int, ...], Unit]:
    match = _INDEXED.match(path)
    if match:
        group, index, field = match.group(1), int(match.group(2)), match.group(3)
        items = link.channel if group == "channel" else link.penalties
        expected = "loss_max" if group == "channel" else "value"
        if field != expected or index >= len(items):
            raise KeyError(f"no input {path!r} in this link")
        if group == "channel":
            return ("channel", index, "loss_max", "value", "value"), "dB"
        return ("penalties", index, "value", "value", "value"), "dB"
    if path not in _FIXED:
        raise KeyError(f"unknown input path {path!r}")
    keys, unit = _FIXED[path]
    if path == "tx.launch_oma_min" and link.tx.launch_oma_min is None:
        raise KeyError("tx.launch_oma_min is derived from tx.upstream in this link")
    if path.startswith("tx.upstream.") and link.tx.upstream is None:
        raise KeyError(f"no input {path!r}: this link has a fixed TP2")
    return keys, unit


def input_unit(link: Link, path: str) -> Unit:
    """Unit of a numeric input. Raises KeyError for an unknown or absent path."""
    return _keys(link, path)[1]


def get_input(link: Link, path: str) -> float:
    keys, _ = _keys(link, path)
    node: Any = link.model_dump(mode="json")
    for key in keys:
        node = node[key]
    return float(node)


def set_input(link: Link, path: str, value: float, provenance: Provenance = EDITED) -> Link:
    """A new Link with the input at path set to value; validated like any other Link."""
    keys, unit = _keys(link, path)
    data: Any = link.model_dump(mode="json")
    parent = data
    for key in keys[:-1]:
        parent = parent[key]
    if unit == "count":
        if float(value) != int(value):
            raise ValueError(f"{path} must be an integer, got {value!r}")
        parent[keys[-1]] = int(value)
    else:
        parent[keys[-1]] = float(value)
    # The Quantity that owns the number is the first dict on the way down with a provenance.
    owner = data
    for key in keys:
        if isinstance(owner, dict) and "provenance" in owner:
            break
        owner = owner[key]
    owner["provenance"] = provenance.model_dump(mode="json")
    return Link.model_validate(data)
