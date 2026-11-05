"""Alembic runs against the database in the app's settings, never one from alembic.ini.

Migrations are plain SQL (`op.execute`). Every table is declared in its feature's `tables.py`:
that metadata is what `alembic revision --autogenerate` compares the database with, to draft a
migration. Run it on a throwaway database only (see the `api-backend` skill).
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

import python_template.tables  # noqa: F401
from python_template import config, db_metadata

if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name, disable_existing_loggers=False)


_COMPARE = {
    "target_metadata": db_metadata.metadata,
    "include_object": db_metadata.include_object,
    "compare_type": True,
    "compare_server_default": True,
}


def _url() -> str:
    # The app speaks psycopg directly; SQLAlchemy needs to be told the driver.
    url = context.config.attributes.get("database_url") or config.settings.database_url

    return url.replace("postgresql://", "postgresql+psycopg://", 1)


def run_migrations_offline() -> None:
    context.configure(url=_url(), literal_binds=True, **_COMPARE)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, **_COMPARE)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
