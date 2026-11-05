"""The tables declared in the features' `tables.py` match what the migrations build."""

import collections.abc
import typing

import pytest
import sqlalchemy
import sqlalchemy.dialects.postgresql

import python_template.tables  # noqa: F401
import metadata_helpers
from python_template import db_metadata


@pytest.fixture
def connection(
    migrated_postgres: tuple[str, str | None],
) -> collections.abc.Iterator[sqlalchemy.Connection]:
    url, _ = migrated_postgres
    engine = sqlalchemy.create_engine(url.replace("postgresql://", "postgresql+psycopg://", 1))

    with engine.connect() as connection:
        yield connection


# Not declared on purpose: Alembic's own bookkeeping table.
_UNDECLARED_TABLES = {"alembic_version"}


def test_every_table_in_the_database_is_declared(connection: sqlalchemy.Connection) -> None:
    in_database = set(sqlalchemy.inspect(connection).get_table_names()) - _UNDECLARED_TABLES

    assert in_database == set(db_metadata.metadata.tables)


def test_declared_tables_match_the_migrations(connection: sqlalchemy.Connection) -> None:
    differences = metadata_helpers.list_autogenerate_differences(
        connection, db_metadata.metadata, db_metadata.include_object
    )

    assert differences == []


def test_declared_checks_not_valid_keys_and_partial_indexes_match_the_migrations(
    connection: sqlalchemy.Connection,
) -> None:
    differences = metadata_helpers.list_unchecked_differences(connection, db_metadata.metadata)

    assert differences == []


# What migrations do that is hard to declare, tried on throwaway tables that are rolled back. Each
# case is a declaration of `probe_child`, and whether the two comparisons then report a difference
# from the DDL below.
_PROBE_DDL = """
CREATE TABLE probe_parent (a text NOT NULL, b integer NOT NULL, PRIMARY KEY (a, b));
CREATE TABLE probe_child (
    id text PRIMARY KEY, pa text, pb integer, name text,
    tags text[] DEFAULT '{}' NOT NULL,
    CONSTRAINT probe_child_name_check CHECK (name <> ''::text)
);
ALTER TABLE probe_child ADD CONSTRAINT probe_child_parent_fkey
    FOREIGN KEY (pa, pb) REFERENCES probe_parent (a, b) NOT VALID;
CREATE UNIQUE INDEX probe_child_name_key ON probe_child (name) WHERE name IS NOT NULL;
"""


def _declare_probe_tables(
    *,
    not_valid: bool = True,
    where: bool = True,
    tags_default: bool = True,
    composite: bool = True,
    check: str = "right",
) -> sqlalchemy.MetaData:
    probe = sqlalchemy.MetaData(naming_convention=db_metadata.NAMING_CONVENTION)
    sqlalchemy.Table(
        "probe_parent",
        probe,
        sqlalchemy.Column("a", sqlalchemy.Text, primary_key=True),
        sqlalchemy.Column("b", sqlalchemy.Integer, primary_key=True),
    )
    sqlalchemy.Table(
        "probe_child",
        probe,
        sqlalchemy.Column("id", sqlalchemy.Text, primary_key=True),
        sqlalchemy.Column("pa", sqlalchemy.Text),
        sqlalchemy.Column("pb", sqlalchemy.Integer),
        sqlalchemy.Column("name", sqlalchemy.Text),
        sqlalchemy.Column(
            "tags",
            sqlalchemy.dialects.postgresql.ARRAY(sqlalchemy.Text),
            nullable=False,
            server_default=sqlalchemy.text("'{}'") if tags_default else None,
        ),
        *(
            [
                sqlalchemy.ForeignKeyConstraint(
                    ["pa", "pb"],
                    ["probe_parent.a", "probe_parent.b"],
                    name="probe_child_parent_fkey",
                    postgresql_not_valid=not_valid,
                )
            ]
            if composite
            else []
        ),
        *(
            [
                sqlalchemy.CheckConstraint(
                    "name <> ''::text" if check == "right" else "name <> 'x'::text", name="name"
                )
            ]
            if check != "omitted"
            else []
        ),
        sqlalchemy.Index(
            "probe_child_name_key",
            "name",
            unique=True,
            postgresql_where=sqlalchemy.text("name IS NOT NULL") if where else None,
        ),
    )

    return probe


@pytest.mark.parametrize(
    ("declared", "autogenerate_differs", "unchecked_differs"),
    [
        pytest.param({}, False, False, id="all declared"),
        pytest.param({"tags_default": False}, True, False, id="array default left out"),
        pytest.param({"composite": False}, True, True, id="composite key left out"),
        # Autogenerate does not compare these, so only the second comparison catches a wrong
        # declaration.
        pytest.param({"not_valid": False}, False, True, id="NOT VALID left out"),
        pytest.param({"where": False}, False, True, id="partial index declared as a full one"),
        pytest.param({"check": "wrong"}, False, True, id="CHECK with other text"),
        pytest.param({"check": "omitted"}, False, True, id="CHECK left out"),
    ],
)
def test_awkward_constraints(
    connection: sqlalchemy.Connection,
    declared: dict[str, typing.Any],
    autogenerate_differs: bool,
    unchecked_differs: bool,
) -> None:
    probe = _declare_probe_tables(**declared)

    transaction = connection.begin()
    connection.execute(sqlalchemy.text(_PROBE_DDL))
    autogenerate = metadata_helpers.list_autogenerate_differences(
        connection,
        probe,
        lambda obj, name, type_, reflected, compare_to: (
            name if type_ == "table" else obj.table.name
        )
        in probe.tables,
    )
    unchecked = metadata_helpers.list_unchecked_differences(connection, probe)
    transaction.rollback()

    assert (bool(autogenerate), bool(unchecked)) == (autogenerate_differs, unchecked_differs)
