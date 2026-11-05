# ADR-0001: One import package under `src/`, named after the project

**Status:** accepted
**Date:** 2026-10-28
**Source:** the template's initial layout (`docs/LAYOUT.md`)

## Context

Code that sits in several top-level folders, or in a package at the repository root, can be imported
from the working directory without being installed. Tests and notebooks then pass while the built
wheel misses a file, and nothing says which folder is the product. The Python Packaging Authority
recommends the `src/` layout for this reason. It is also the default nothing here argues against.

## Decision

- All product code lives in one import package, `src/<package>/`. The distribution name is kebab
  case (`my-project`), the import name is snake case (`my_project`).
- Nothing outside that package is imported by name. Tests, scripts and notebooks import the
  installed package.
- The package is installed in editable mode by `make bootstrap`.

## Alternatives rejected

- A package at the repository root (flat layout): imports work without installing, so a file
  missing from the wheel goes unnoticed. It is simpler for notebooks, and the editable install
  gives the same result.
- Several top-level packages: there is no single public surface, and it is unclear what ships.

## Consequences

- Run `make bootstrap` before tests, so the package is importable.
- The packaging line in `pyproject.toml` names the folder: `from = "src"`.
- Renaming the project means renaming the folder too. `scripts/rename_project.py` does it.
