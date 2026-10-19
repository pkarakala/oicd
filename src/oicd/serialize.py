"""Deterministic JSON for every API response: sorted keys, compact separators, Python's
shortest round-trip float repr. NaN and infinity are rejected (allow_nan=False)."""

import json

from pydantic import BaseModel


def canonical_json(model: BaseModel) -> str:
    return json.dumps(
        model.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
