# ADR-NNNN: Tables are declared in code and checked against the migrations

**Status:** accepted
**Date:** YYYY-MM-DD
**Source:** <ticket or commit where the team agreed>
**Follows:** ADR-<only the owning feature writes a table>

<!-- Draft from the api-backend skill. Edit it to fit the project, then copy it to docs/decisions/
under the next free number. Propose it to the user first (docs skill). -->

## Context

The schema is visible only in migrations and in the `schema.sql` dump. A column renamed in a
migration is not caught anywhere in Python, and the owner of a table cannot be read from the code.
Alembic can compare a SQLAlchemy Core `MetaData` with a migrated database. It does not compare
CHECK constraints, the NOT VALID flag or partial-index predicates, but the inspector reports them
and a second check can compare them. Declaring the tables next to the migrations is the smallest
option that gives all of this.

## Decision

- Every table is a SQLAlchemy Core `Table` in `features/<x>/tables.py` of its owning feature, on
  the shared `MetaData` in `db_metadata.py`. Cross-feature keys are strings
  (`ForeignKey("note.id")`); features do not import each other's tables. `tables.py` imports all
  of them.
- The migrations stay the source of truth for the database. `schema.sql` stays as their dump.
- `tests/test_metadata.py` fails when a table is not declared, or when Alembic autogenerate or the
  second check (CHECK name and text, NOT VALID, partial predicates) finds a difference from the
  migrated database.
- A new migration starts from autogenerate on a throwaway database and is edited by hand.
  CHECKs, NOT VALID, partial predicates, constraint comments, extensions and data steps are
  written by hand. Table and column comments are declared with `comment=` and compared.
- Store queries stay raw SQL.

## Alternatives rejected

- The metadata as the source of truth, with the app creating tables: gives up reviewed, ordered
  migrations and data steps.
- Declarations generated from the database: nothing in the code to read, and nothing to check
  against.
- SQLAlchemy Core queries in the stores: people who know SQL but not Python find them harder to
  read.
- One central module for all tables: ownership would not be visible per feature.

## Consequences

- A schema change touches three files, and the tests fail when they disagree: the declaration, the
  migration and `schema.sql`.
- A CHECK is declared with the text Postgres reports, so a reformatted CHECK needs the
  declaration updated too.
