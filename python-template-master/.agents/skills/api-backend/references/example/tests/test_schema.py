"""The committed schema.sql is what the migrations build, dumped by Postgres itself."""

import os
import pathlib
import re
import subprocess

import pytest

SCHEMA = pathlib.Path(__file__).resolve().parent.parent / "schema.sql"

# Lines that differ between runs or pg_dump builds: the version banner and the random \restrict
# key.
_VOLATILE = re.compile(r"^(-- Dumped (from database|by pg_dump) version .*|\\(un)?restrict .*)$")


def test_committed_schema_matches_the_migrations(migrated_postgres: tuple[str, str | None]) -> None:
    _, container = migrated_postgres
    if container is None:
        pytest.skip("pg_dump runs inside the throwaway container, and TEST_DATABASE_URL has none")

    dump = subprocess.run(
        [
            "docker", "exec", container,
            "pg_dump", "-U", "app", "--schema-only", "--no-owner", "--no-privileges", "app_test",
        ],
        capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip

    # Shaped the way the end-of-file and trailing-whitespace hooks leave a committed file.
    lines = [line.rstrip() for line in dump.splitlines() if not _VOLATILE.match(line)]
    schema = "\n".join(lines).strip("\n") + "\n"

    if os.environ.get("UPDATE_SCHEMA") == "1":
        SCHEMA.write_text(schema)
        return

    assert (
        SCHEMA.exists() and SCHEMA.read_text() == schema
    ), "the schema changed: run `make schema` and commit it"
