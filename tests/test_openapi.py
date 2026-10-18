"""web/openapi.json (the input of `npm run gen:api`) must match the API, so the generated
web/src/api/schema.ts is never stale."""

from pathlib import Path

from scripts.dump_openapi import openapi_text

ROOT = Path(__file__).resolve().parents[1]


def test_committed_openapi_matches_the_api():
    committed = (ROOT / "web" / "openapi.json").read_text(encoding="utf-8")
    assert committed == openapi_text(), "run `npm run gen:api` in web/"
