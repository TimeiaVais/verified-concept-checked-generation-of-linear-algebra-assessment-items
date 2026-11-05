---
name: api-backend
description: Build or change an API service with a Postgres database. Covers the feature-folder layout, API model names, tables owned by one feature, Alembic migrations, and generated files (openapi.json, schema.sql) with tests that fail when they are stale. Load when the project serves an HTTP API or owns a database schema, or when asked to add an endpoint, a table or a migration. Skip it for libraries and training code.
compatibility: universal
---

# API backend

Optional skill. Delete it, its symlink in `.claude/skills/` and its line in `AGENTS.md` if the
project is not a service. It builds on `docs/LAYOUT.md`: one package, thin edges, one-way
dependencies.

The stack in the recipes is FastAPI, Postgres (psycopg, raw SQL in the stores), SQLAlchemy Core
(table declarations only) and Alembic. The rules hold for another web framework. The recipes do not.

## Layout of a service

```
src/<package>/
  config.py        settings, read once from the environment
  main.py          the FastAPI app; includes each feature's router
  db_metadata.py   the SQLAlchemy metadata (not used at runtime)
  tables.py        imports every feature's tables.py
  infra/           edge code: the database connection, HTTP clients, storage
  features/<x>/    router.py, schemas.py, store.py, tables.py
migrations/        Alembic (repo root), with alembic.ini next to it
openapi.json       generated, committed
schema.sql         generated, committed
```

- A router calls a store. A store runs SQL through a connection from `infra/`. Nothing in
  `infra/` imports a feature.
- Features do not import each other's `tables.py`. A key to another feature's table is a string:
  `ForeignKey("note.id")`.
- A feature that needs another feature's data calls the owner's store function, and passes its
  connection when both changes must be one transaction.

## Start a service

Run the steps from the repository root. If you renamed the project first, the files below already
use your package name. If not, replace `python_template` in them.

1. `poetry add fastapi "psycopg[binary]" sqlalchemy alembic`. Add `uvicorn` to serve the app.
2. Copy the example:
   ```sh
   S=.agents/skills/api-backend/references/example
   cp -r $S/package/. src/<package>/
   cp -r $S/root/. .
   cp -r $S/tests/. tests/
   ```
3. Add the targets in `.agents/skills/api-backend/references/Makefile.fragment` to the `Makefile`,
   and their names to `.PHONY`.
4. `make openapi` and `make schema`. Commit `openapi.json` and `schema.sql`.
5. `make test`. It needs docker, or `TEST_DATABASE_URL` set to a database you can wipe.
6. Replace the `notes` feature with the first real one: its tables, its migration, its router.
   Keep the folder shape.
7. Propose the three ADRs in `references/adr/` to the user (the `docs` skill: propose first, write
   after the user agrees). They explain the rules below.

## API models

Name API schemas by direction.

- A request body is `...Request`, a response model is `...Response` (`CreateUserRequest`,
  `UserResponse`). `...In` is for internal job inputs only, never an API body.
- A multipart body gets an explicit form model (`typing.Annotated[UploadRequest, fastapi.Form()]`),
  not loose `File` and `Form` parameters, so FastAPI does not invent a `Body_…` name.
- When a model is also used inside (stores, jobs, scripts), keep the internal name and return
  `class XResponse(X)` with `__doc__ = X.__doc__` from the router. This subclass is the one allowed
  exception to the composition rule in the `python` skill and needs no comment. A model used only
  by the API is renamed in place. Nested models keep their names.

## Tables

- Each table has one owning feature: the feature whose `tables.py` declares it. Only the owner
  writes it. Others call the owner's store functions. `tests/test_table_owners.py` checks this.
- A new table follows the conventions in `references/adr/conventions-for-new-tables.md` (ids, keys,
  status checks, comments).

## Change the schema

1. Edit the `Table` in the owning feature's `tables.py`.
2. Run autogenerate on a **throwaway** database at `head`, never a shared one
   (`compare_server_default` can call `nextval` and use up sequence values):
   `alembic revision --autogenerate -m "…"`.
3. Rewrite the draft by hand. Migrations are plain SQL in `op.execute`. To see the SQL of a draft
   first: `alembic upgrade <previous revision>:<new revision> --sql`.
4. `make schema`. Commit the declaration, the migration and `schema.sql` together.
   `tests/test_metadata.py` fails if they disagree.

Autogenerate drafts. It does not decide. A rename comes out as a drop and an add. A new `NOT NULL`
column on a table with rows needs a default or a backfill, or the migration fails on real data.

Always written by hand, whatever autogenerate says: CHECK constraints (declared in `tables.py`
with the text Postgres reports), `NOT VALID` foreign keys and their later `VALIDATE CONSTRAINT`,
partial-index predicates, `COMMENT ON CONSTRAINT`, extensions, data backfills and renames. A
table or column comment is declared with `comment=`, and must match the migration's `COMMENT ON`.

## Generated files

`openapi.json` and `schema.sql` are generated and committed. A test fails while either is stale:

- `make openapi` after any change to routes or models.
- `make schema` after any migration.

Do not edit them by hand. If the project generates more (a typed client, a diagram), give each the
same pair: a `make` target and a test or `--check` that fails while it is stale.

## What the recipes are

All in `references/example/`.

- `package/`: a working example feature (`notes`) with the wiring around it: `config.py`,
  `db_metadata.py`, `tables.py`, `main.py`, `infra/db.py`.
- `root/`: `alembic.ini`, `migrations/env.py` and the first migration.
- `tests/conftest.py`: a throwaway Postgres in docker, migrated by the real migrations, and an
  `empty_database` fixture. It uses `TEST_DATABASE_URL` instead when that is set.
- `tests/test_openapi.py`, `tests/test_schema.py`: the two staleness checks.
- `tests/test_metadata.py` and `metadata_helpers.py`: declared tables against the migrated
  database, including the CHECK, NOT VALID and partial-index cases autogenerate skips.
- `tests/test_table_owners.py`: the owner rule. It has a scan of the strings in `features/`.
- `tests/test_notes_store.py`: an example store test.

## Verified

Run on 2026-10-28 in a scratch project made from this template: renamed, then steps 1 to 5 above.
Versions installed: fastapi 0.162.0, psycopg 3.3.6, SQLAlchemy 2.1.6, Alembic 1.20.1, pydantic
2.14.1, Postgres 17 in docker.

- `make lint` clean (black, isort, ruff, mypy), and 20 tests pass, including the example's.
- Each check fails for the violation it guards: a stale `openapi.json`, a stale `schema.sql`, a
  declaration that disagrees with a migration, and a feature that writes another feature's table.
  `make schema` then fixes the stale dump.
- The first run found one error in the example itself: the migration commented the table, the
  declaration did not. `test_metadata.py` caught it.
- `tests/test_table_owners.py` is new code. The rule was written down in the source project but
  nothing tested it. It was tried only on the example and on the three violations above.
- Not tried: another Postgres version, a `TEST_DATABASE_URL` run, and a project with several
  features that reference each other.

Run the steps again, and update this section, when a version above changes.
