# ADR-0003: Tests live outside the package

**Status:** accepted
**Date:** 2026-10-28
**Source:** the template's initial layout (`docs/LAYOUT.md`)
**Follows:** ADR-0001

## Context

Tests inside the package ship in the wheel, are importable by users, and count toward coverage of
the product. Tests outside it show what a user of the installed package sees. This is the default
nothing here argues against.

## Decision

- Tests are in `tests/`, next to `src/`, and the folder tree mirrors the package tree.
- Tests import the installed package (ADR-0001). They never import from `src/` by path.
- A slow test, or one that needs a network or another external service, carries
  `@pytest.mark.slow`. pytest runs with `--strict-markers`, so a misspelled marker fails.

## Alternatives rejected

- Tests inside the package: they would be part of the wheel, and fixtures would be visible to users.
- Doctests as the main tests: they document, but they do not fit fixtures or parametrised cases.

## Consequences

- A fast run is `pytest -m "not slow"`. `make test` runs everything.
- Test helpers live in `tests/`, and the package never imports them.
- `scripts/rename_project.py` has its own test, which it deletes with itself.
