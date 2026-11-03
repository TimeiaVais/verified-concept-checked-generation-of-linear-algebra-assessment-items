# ADR-0002: Absolute imports and a typed package

**Status:** accepted
**Date:** 2026-10-28
**Source:** the template's initial layout (`docs/LAYOUT.md`)
**Follows:** ADR-0001

## Context

A relative import breaks when a module moves, and reads differently in the package, in a script and
in a test. Untyped functions hide the mistakes that a type checker finds before a run. A data or
model pipeline is the worst place for them: a wrong type shows up hours into a job.

## Decision

- Imports are absolute: `from my_project import module`. No relative imports.
- Every function and method is fully annotated. `mypy` runs with `disallow_untyped_defs` in
  `make lint` and in the commit hook, on `src/`.
- The package ships a `py.typed` marker, so projects that depend on it see its types.

## Alternatives rejected

- Relative imports: shorter inside one package, but the cost above grows with the package.
- Types on public functions only: private helpers are where most of the logic is.

## Consequences

- Moving a module means updating its imports. An IDE rename does this.
- A commit with a missing annotation fails the hook. Tests are exempt from the annotation rule.
- The marker is checked by `tests/test_package.py`.
