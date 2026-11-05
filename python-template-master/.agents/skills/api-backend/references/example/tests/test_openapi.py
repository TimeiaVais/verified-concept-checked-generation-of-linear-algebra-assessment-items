"""The committed API schema is the one the app serves."""

import json
import pathlib

from python_template.main import app

OPENAPI = pathlib.Path(__file__).resolve().parent.parent / "openapi.json"


def test_committed_openapi_schema_matches_the_app() -> None:
    committed = json.loads(OPENAPI.read_text())

    assert committed == app.openapi(), "the API changed: run `make openapi` and commit it"
