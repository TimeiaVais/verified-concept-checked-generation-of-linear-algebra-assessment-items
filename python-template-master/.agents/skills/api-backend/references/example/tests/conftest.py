"""A real Postgres for the tests that need one, migrated by the real migrations.

Without configuration a throwaway Postgres container is started for the session and removed at
its end. To use a database you already run instead:

    TEST_DATABASE_URL=postgresql://app:app@localhost:5432/app_test pytest

It is wiped between tests, so never point this at a database you care about. Tests that ask for
`empty_database` are skipped when neither the variable nor docker is there.
"""

import collections.abc
import contextlib
import os
import pathlib
import shutil
import subprocess
import time

import psycopg
import pytest

from python_template import config

ROOT = pathlib.Path(__file__).resolve().parent.parent
POSTGRES_IMAGE = "postgres:17"


@pytest.fixture(scope="session")
def postgres() -> collections.abc.Iterator[tuple[str, str | None]]:
    """The test database URL and, when a throwaway container runs it, the container id."""
    url = os.environ.get("TEST_DATABASE_URL")

    if url:
        yield url, None
    elif not shutil.which("docker"):
        pytest.skip("TEST_DATABASE_URL not set and docker not found")
    else:
        with _run_postgres() as (container_url, container):
            yield container_url, container


@pytest.fixture(scope="session")
def migrated_postgres(
    postgres: tuple[str, str | None],
) -> collections.abc.Iterator[tuple[str, str | None]]:
    """The same as `postgres`, after `alembic upgrade head`. The app is pointed at it."""
    url, container = postgres
    config.settings.database_url = url
    _upgrade(url)

    yield url, container


@pytest.fixture
def empty_database(migrated_postgres: tuple[str, str | None]) -> str:
    """A migrated database with no rows in any table. Returns its URL."""
    url, _ = migrated_postgres

    with psycopg.connect(url) as connection:
        table_names = [
            row[0]
            for row in connection.execute(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
            )
        ]
        connection.execute(f"TRUNCATE {', '.join(table_names)} RESTART IDENTITY CASCADE")

    return url


@contextlib.contextmanager
def _run_postgres() -> collections.abc.Iterator[tuple[str, str]]:
    container = subprocess.run(
        [
            "docker", "run", "-d", "--rm",
            "-e", "POSTGRES_USER=app", "-e", "POSTGRES_PASSWORD=app", "-e", "POSTGRES_DB=app_test",
            "-p", "127.0.0.1::5432", POSTGRES_IMAGE,
        ],
        capture_output=True, text=True, check=True,
    ).stdout.strip()  # fmt: skip

    try:
        port = (
            subprocess.run(
                ["docker", "port", container, "5432/tcp"],
                capture_output=True,
                text=True,
                check=True,
            )
            .stdout.splitlines()[0]
            .rsplit(":", 1)[1]
        )
        url = f"postgresql://app:app@127.0.0.1:{port}/app_test"
        # The image's init server listens on the socket only, so a TCP connect means the real one
        # is up.
        deadline = time.monotonic() + 60

        while True:
            try:
                psycopg.connect(url).close()
                break

            except psycopg.OperationalError:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.5)

        yield url, container

    finally:
        subprocess.run(["docker", "rm", "-f", container], capture_output=True)


def _upgrade(url: str) -> None:
    from alembic import command
    from alembic.config import Config

    alembic_config = Config(str(ROOT / "alembic.ini"))
    alembic_config.attributes["database_url"] = url

    command.upgrade(alembic_config, "head")
