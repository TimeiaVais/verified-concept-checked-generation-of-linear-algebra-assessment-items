# ADR-NNNN: Only the owning feature writes a table

**Status:** accepted
**Date:** YYYY-MM-DD
**Source:** <ticket or commit where the team agreed>
**Follows:** ADR-<conventions for new tables>, ADR-<tables are declared in code>

<!-- Draft from the api-backend skill. Edit it to fit the project, then copy it to docs/decisions/
under the next free number. Propose it to the user first (docs skill). -->

## Context

Each table is created by one feature, but nothing says that only that feature may write it. A
second writer copies the column list and assumes the lifecycle. When the owner adds a NOT NULL
column or a status, the second writer breaks and nothing points at it. Reads are different: a
reader depends on columns, not on rules.

## Decision

- Every table has one owning feature: the feature whose `tables.py` declares it.
- Only the owner runs `INSERT`, `UPDATE` or `DELETE` on its table. Other features and scripts call
  the owner's store functions, and pass their connection when the change must be part of one
  transaction.
- A script counts as the feature whose store it calls. It does not write tables itself.
- `tests/test_table_owners.py` fails when a feature writes a table it does not own, and when a
  write cannot be resolved to a table. Exceptions are listed in the test, each with a reason.
- Reads across features stay allowed.
- Migrations and the database setup are not features and are not scanned.

## Alternatives rejected

- A convention in AGENTS.md only: nothing notices the first violation.

## Consequences

- A feature that needs a new kind of write on another feature's table asks the owner for a store
  function. This adds a small function and removes a silent coupling.
- The scan reads string constants in `features/`. A table name built at run time fails it, so name
  tables in constants.
