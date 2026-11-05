"""Two comparisons of declared tables (`db_metadata`) with a migrated database.

`list_autogenerate_differences` is Alembic autogenerate. It does not compare CHECK constraints,
the NOT VALID flag of a foreign key or the WHERE of a partial index, so
`list_unchecked_differences` compares those from the database's own catalog. Constraint comments
and extensions have no declaration and are not compared.
"""

import typing

import alembic.autogenerate
import alembic.migration
import sqlalchemy

__all__ = ["list_autogenerate_differences", "list_unchecked_differences"]


def list_autogenerate_differences(
    connection: sqlalchemy.Connection,
    metadata: sqlalchemy.MetaData,
    include_object: typing.Callable[..., bool],
) -> list[typing.Any]:
    """List what Alembic autogenerate would change to make the database match `metadata`."""
    context = alembic.migration.MigrationContext.configure(
        connection,
        opts={
            "include_object": include_object,
            "compare_type": True,
            "compare_server_default": True,
        },
    )
    differences = alembic.autogenerate.compare_metadata(context, metadata)

    return differences


def list_unchecked_differences(
    connection: sqlalchemy.Connection, metadata: sqlalchemy.MetaData
) -> list[str]:
    """List the CHECK, NOT VALID and partial-index differences between `metadata` and the database.

    A declared CHECK or partial-index predicate has to be written the way Postgres reports it: the
    CHECK as the inspector returns it, the predicate without the outer parentheses Postgres adds.
    """
    inspector = sqlalchemy.inspect(connection)
    differences = []

    for table in metadata.sorted_tables:
        declared_checks = {
            constraint.name: _squash(str(constraint.sqltext))
            for constraint in table.constraints
            if isinstance(constraint, sqlalchemy.CheckConstraint)
        }
        actual_checks = {
            check["name"]: _squash(check["sqltext"])
            for check in inspector.get_check_constraints(table.name)
        }
        if declared_checks != actual_checks:
            differences.append(
                f"{table.name}: CHECK declared {declared_checks}, in the database {actual_checks}"
            )

        declared_not_valid = {
            key.name
            for key in table.foreign_key_constraints
            if key.dialect_options["postgresql"]["not_valid"]
        }
        actual_not_valid = {
            name
            for (name,) in connection.execute(
                sqlalchemy.text(
                    "SELECT conname FROM pg_constraint "
                    "WHERE contype = 'f' AND NOT convalidated AND conrelid = to_regclass(:table)"
                ),
                {"table": table.name},
            )
        }
        if declared_not_valid != actual_not_valid:
            differences.append(
                f"{table.name}: NOT VALID declared {sorted(declared_not_valid)}, "
                f"in the database {sorted(actual_not_valid)}"
            )

        declared_predicates = {
            index.name: _squash(f"({index.dialect_options['postgresql']['where']})")
            for index in table.indexes
            if index.dialect_options["postgresql"]["where"] is not None
        }
        actual_predicates = {
            index["name"]: _squash(index["dialect_options"]["postgresql_where"])
            for index in inspector.get_indexes(table.name)
            if index["name"] in {declared.name for declared in table.indexes}
            and "postgresql_where" in index["dialect_options"]
        }
        if declared_predicates != actual_predicates:
            differences.append(
                f"{table.name}: partial index declared {declared_predicates}, "
                f"in the database {actual_predicates}"
            )

    return differences


def _squash(text: str) -> str:
    squashed = " ".join(text.split())

    return squashed
