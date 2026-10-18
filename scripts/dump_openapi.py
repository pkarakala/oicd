"""Write the API's OpenAPI schema as stable JSON (sorted keys) for openapi-typescript.

Usage: uv run python scripts/dump_openapi.py web/openapi.json
"""

import json
import sys
from pathlib import Path

from oicd.api import app


def openapi_text() -> str:
    return json.dumps(app.openapi(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    Path(sys.argv[1]).write_text(openapi_text(), encoding="utf-8")
