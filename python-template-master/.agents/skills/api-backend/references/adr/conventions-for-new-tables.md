# ADR-NNNN: Conventions for new tables

**Status:** accepted
**Date:** YYYY-MM-DD
**Source:** <ticket or commit where the team agreed>

<!-- Draft from the api-backend skill. Edit it to fit the project, then copy it to docs/decisions/
under the next free number. Propose it to the user first (docs skill). -->

## Context

Tables created at different times differ in how their ids are made and which references the
database enforces. A reference that only the code checks is not found by any tool, and it breaks
on the first row that disagrees. Fixing the shape before a table holds data costs a line. Fixing
it after costs a backfill.

## Decision

Every new table:

- has `id TEXT PRIMARY KEY`, made by the application with one scheme for all tables;
- has `created_at TIMESTAMPTZ NOT NULL`;
- has a foreign key to every parent row it names. A parent row is not deleted while a child
  refers to it, unless the migration says `ON DELETE CASCADE` and why;
- has a `status` column with a CHECK constraint when it has a lifecycle;
- has `COMMENT ON TABLE`, and a comment on every column or constraint whose purpose is not clear
  from its name;
- keeps large files outside the database and stores their path or key, never `BYTEA`.

## Alternatives rejected

- References checked in code: nothing enforces them, and tools cannot follow them.

## Consequences

- `schema.sql` shows every constraint, so a reviewer checks a new table against this list.
- A hard delete of a parent row fails while children exist. Deleting needs a decision.
