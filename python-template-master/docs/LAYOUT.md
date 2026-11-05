# Layout

How the repository and the package are organized. The same rules fit a library, a service, a
command line tool and a data science project. They are all Python projects with one package.
The reasons for the main rules are in `docs/decisions/` (ADR-0001 to ADR-0003).

## The repository

```
pyproject.toml     project metadata, dependencies, and the settings of every tool
Makefile           bootstrap, lint, test, build, clean, lock
src/<package>/     all product code (one import package)
tests/             tests, mirroring the package tree
scripts/           optional: one-off tools, thin, no logic of their own
docs/              LAYOUT, ARCHITECTURE, glossary, decisions, backlog, done
configs/           optional: config files for runs and experiments
notebooks/         optional: exploration and reports
data/              optional, not in git: input data
artifacts/         optional, not in git: models, outputs, build products
```

A folder appears when the project needs it. Do not create an empty `utils/` or `common/` to fill
the picture.

## Rules

1. **One import package, named after the project.** All product code is in `src/<package>/`. The
   distribution name is `my-project`, the import name is `my_project`. Nothing outside the package
   is imported by name. (ADR-0001)
2. **Tests are outside the package.** `tests/` mirrors the package tree. Slow tests, and tests that
   need a network, carry `@pytest.mark.slow`. (ADR-0003)
3. **Scripts stay thin.** A command line entry point is declared in `[project.scripts]` in
   `pyproject.toml` and calls a function in the package. A file in `scripts/` parses its
   arguments and calls the package. Logic that a test needs goes in the package.
4. **Group by domain, not by type.** `training/` and `evaluation/` are domains. `models/`,
   `helpers/` and `utils/` are types. A module name says what the module holds (see "Naming" in
   `AGENTS.md`).
5. **Dependencies point one way.** The edge of the program (command line, config, file and network
   access) calls the middle (the logic), and the middle calls the pure core (functions of their
   inputs). A lower layer never imports a higher one. The logic runs in a test with no files and
   no network.
6. **Typed, with absolute imports.** `py.typed` is in the package, every function is annotated,
   imports are absolute. Public modules define `__all__`. (ADR-0002)
7. **One place reads the configuration.** A `config` module reads environment variables or a
   config file once and passes values down. Deep code does not read `os.environ`.
8. **Data and artifacts stay out of git.** `data/` and `artifacts/` are in `.gitignore`. Large
   files live in a storage bucket, DVC or a model registry. Code takes their paths from the
   configuration, not from constants.

## Inside the package

Start with one module and split when it has two reasons to change. Examples of the first split,
by kind of project:

- A library: one module per public concept (`parsing.py`, `validation.py`), plus a short
  `__init__.py` that exports the public names.
- A service or command line tool: `cli.py` or `app.py` at the edge, `config.py`, then one
  sub-package per domain (`accounts/`, `billing/`).
- A data science or model training project: `data/` for loading and splitting, `features/`,
  `training/`, `evaluation/`, and `config.py`. A run is one function that takes a config and
  returns its outputs.

Do not move to several packages in one repository unless two parts must be installed and
versioned separately. If they must, make a second repository or a workspace, not a second
top-level folder in `src/`.

## Data and experiments

- Notebooks import the package. They hold exploration and charts, not logic. When a cell is worth
  keeping, move it into the package and test it. Strip outputs before commit: add the
  `nbstripout` hook to `.githooks.yml` when the first notebook arrives.
- A run is reproducible from its config. Put the seed, the data version and the parameters in a
  file under `configs/`, and write them next to the outputs in `artifacts/`.
- Name an output by the run that made it (`artifacts/2026-10-28-baseline/`), not by `final` or
  `new`.
- Keep a small sample of the data in `tests/` for tests (a few rows, not the real file).

## Files that tools read

- `pyproject.toml`: packaging and the settings of black, isort, ruff, mypy, pytest and coverage.
  Line length is 100 everywhere.
- `.githooks.yml`: the git hooks. `make bootstrap` installs them, `make lint` runs all of them.
- `.editorconfig`, `.gitlint`, `.gitignore`, `poetry.toml`: editor, commit message, ignore and
  virtual environment settings.
