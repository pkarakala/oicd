"""Load Link profiles from JSON files (profiles/ at the repo root by default)."""

import re
from pathlib import Path

from oicd.schema import Link

# src/oicd/profiles.py -> repo root.
PROFILES_DIR = Path(__file__).resolve().parents[2] / "profiles"

_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def load_link(path: Path | str) -> Link:
    return Link.model_validate_json(Path(path).read_text(encoding="utf-8"))


def profile_path(name: str, directory: Path = PROFILES_DIR) -> Path:
    """Path of profiles/<name>.json. Names are restricted to [A-Za-z0-9_-] so a name can never
    point outside the profiles directory. Raises FileNotFoundError if there is no such profile."""
    if not _NAME_RE.match(name):
        raise FileNotFoundError(f"invalid profile name {name!r}")
    path = directory / f"{name}.json"
    if not path.is_file():
        raise FileNotFoundError(f"no profile named {name!r}")
    return path
