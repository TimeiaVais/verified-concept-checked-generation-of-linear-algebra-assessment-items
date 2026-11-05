"""The SQLAlchemy metadata every feature's `tables.py` declares its tables on.

The metadata is not used at runtime: stores run raw SQL. It exists so that Alembic autogenerate can
compare the migrations against it (`migrations/env.py`, `tests/test_metadata.py`). The naming
convention reproduces the constraint names Postgres and the migrations use, so a declared table
needs no explicit names.
"""

import typing

import sqlalchemy

__all__ = ["NAMING_CONVENTION", "include_object", "metadata"]

NAMING_CONVENTION: typing.Final[dict[str, str]] = {
    "pk": "%(table_name)s_pkey",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
}

metadata = sqlalchemy.MetaData(naming_convention=NAMING_CONVENTION)


def include_object(
    obj: typing.Any, name: str | None, type_: str, reflected: bool, compare_to: typing.Any
) -> bool:
    """Alembic's `include_object` hook: compare only the tables declared here.

    This leaves out `alembic_version`, which autogenerate would otherwise propose to drop.
    """
    table_name = name if type_ == "table" else obj.table.name
    is_declared = table_name in metadata.tables

    return is_declared
