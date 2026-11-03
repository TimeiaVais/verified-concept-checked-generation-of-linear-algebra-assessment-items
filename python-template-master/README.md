# Python template

A starting point for a Python project. It gives you one package, strict tooling, a set of agent
skills, and a docs workflow. It fits a library, a service, a command line tool and a data science
project. They are all the same kind of project here: Python code in one package.

You need Python 3.11 or newer, [Poetry](https://python-poetry.org/) 2, `git` and `make`.

## Start a new project

1. Copy the template into a new folder and start a git repository there. On a hosting site, use
   "Use this template".
2. Commit the copy as it is. The next step rewrites files in place and keeps no backup.
3. Rename the project. The name is lowercase words joined by hyphens:

   ```sh
   python3 scripts/rename_project.py my-project
   ```

   The script replaces the placeholder project name and package name in every text file, renames
   the folder under `src/`, and deletes itself and its test. It does not touch `.git`.
4. Check the result by hand. Run `git diff` and read it. Look at `pyproject.toml` (the
   description) and `docs/glossary.md`.
5. Replace this README with the README of your project. This one describes the template.
6. Install and check: `make bootstrap`, then `make lint` and `make test`. Commit `poetry.lock`.
7. Fill in `pyproject.toml`: `authors` and `license`. Add dependencies with
   `poetry add <package>`.
8. Remove what you do not need (see "Optional parts").

## What each part does

**Agent instructions**
- `AGENTS.md`: the rules for any coding agent here: honesty, naming, simplicity, small changes,
  plan before code, output style, commit messages. Edit it to fit the project.
- `CLAUDE.md`: points Claude Code to `AGENTS.md`.
- `.agents/skills/<name>/SKILL.md`: one skill per topic. An agent loads a skill when the task
  matches its description. `.claude/skills/<name>` is a symlink to each, so Claude Code finds them.
  - `python`: code style and conventions.
  - `docs`: how to work with `docs/` and ADRs (see "Working with docs/").
  - `api-backend`: for a service with an HTTP API and a database. It has the feature-folder layout,
    API model names, table ownership, migration rules, and tested example code in `references/`
    (see "Optional parts").
  - `investigation`: how to read and search the code without wasting effort.
  - `pycharm-tools`: use the IDE's tools when the PyCharm MCP server is connected.
  - `jira`: read and write Jira issues. `jira.py` is the client.
- `.claude/jira.example.json` and `.claude/jira.env.example`: templates for the Jira config and
  token. The real files are in `.gitignore`.

**Tooling**
- `pyproject.toml`: project metadata, dependency groups (`dev`, `tests`), and the settings of
  black, isort, ruff, mypy, pytest and coverage. Line length is 100.
- `Makefile`: `make bootstrap` (environment and git hooks), `lint`, `test`, `build`, `clean`,
  `lock`. A `Makefile.local` is included when it exists, for your own settings. It is not in git.
- `.githooks.yml`: git hooks (basic file checks, black, isort, ruff, mypy, gitlint). They run on
  `git commit`.
- `.gitlint`: commit message rules (title 10 to 72 characters, body lines up to 100).
- `.editorconfig`, `.gitignore`, `poetry.toml`: editor settings, ignored files (it excludes `data/`
  and `artifacts/`), and the virtual environment in `.venv/`.

**Code**
- `src/<package>/`: the product code. It ships `py.typed`.
- `tests/`: tests. `tests/test_package.py` checks the typing marker.
- `scripts/rename_project.py`: the one-shot rename tool. It is gone after step 3.

**Docs**
- `docs/LAYOUT.md`: how the repository and the package are organized, with the reasons.
- `docs/ARCHITECTURE.md`: how the system works today. Starts as an outline.
- `docs/glossary.md`: your domain terms. One concept, one word.
- `docs/decisions/`: ADRs, the record of why. `TEMPLATE.md` is the format. ADR-0001 to 0003 are
  the template's starting decisions. Your project owns them: change them with a new ADR.
- `docs/backlog/` and `docs/done/`: work in progress and finished work (next section).

## Daily work

- `make test`: run the tests with coverage.
- `make lint`: run every hook on every file. Commits run the same hooks on the changed files.
- `make build`: build the wheel and the sdist in `dist/`.
- `make clean`: remove `.venv/`, build output and caches. `make bootstrap` brings it back.
- `make lock`: update `poetry.lock` after you change dependencies by hand.
- Commit messages: imperative subject, 50 to 72 characters, no body unless the reason is not
  clear from the diff. gitlint checks this.

## Working with docs/

An idea goes from a conversation to shipped code in a fixed path. Each step leaves a file that
the next step uses. The `docs` skill makes agents follow the same path.

1. **Brainstorm.** Talk it through with the team or the agent. No code yet. If the problem fits
   one ticket, write the ticket in your tracker and stop here. It does not need a doc.
2. **Create a backlog entry.** Put a file in `docs/backlog/`. The name is
   `YYYY-MM-DD-TYPE_NAME.md`: the day you create it, a type, and the topic. The type is
   `PROPOSAL` for a design to discuss, `HANDOFF` for work to hand to an implementer, or `TICKET`
   for a ticket-sized item that needs a doc. There is no running number, so two branches never
   collide. The date never changes, even when the doc moves.

   ```markdown
   # Proposal: cache the feature table

   **Status (2026-10-28):** not started.

   ## Problem
   ## Options
   ## Recommendation
   ## Open questions
   ```
3. **Iterate on the entry.** Review it, change it, answer the open questions. The entry is the
   plan the agent reads before it designs anything. Every ADR the work touches is named in it.
4. **Implement.** Work in phases. Update the status line in the same change that changes the
   state, for example `**Status (2026-11-02):** partial. Built: loader (a1b2c3d). Open: cache.`
5. **Record decisions.** When a choice could be undone later by someone who does not know why it
   was made, write an ADR. The agent proposes the draft in its reply, and you approve before it
   writes the file. An accepted ADR is never edited. A change is a new ADR that supersedes,
   amends or retires the old one.
6. **Finish and move to `docs/done/`.**
   - Set the status line to `**Done:** <commit>`. Keep the old status after it.
   - Propose ADRs for the decisions that pass the bar in step 5.
   - If modules or flows changed, update `docs/ARCHITECTURE.md`.
   - Put work left over into a ticket, or into a new proposal when it needs brainstorming.
   - Move the file with `git mv`, then fix links to it.

Where a detail goes: a note about one spot in the code is a comment there. A rule that spans
modules is an ADR. A temporary state is a status line. What git log already says goes nowhere.
The full rules are in `.agents/skills/docs/SKILL.md`.

## Optional parts

- **API backend skill.** For a service, follow the "Start a service" steps in
  `.agents/skills/api-backend/SKILL.md`. They copy a working FastAPI + Postgres + Alembic example
  into `src/<package>/`, `tests/` and the repository root, and add `make openapi` and
  `make schema`. Tests fail while `openapi.json` or `schema.sql` is stale. Docker is needed for the
  tests, or a database in `TEST_DATABASE_URL`. For a library or a training project, delete
  `.agents/skills/api-backend/`, its symlink `.claude/skills/api-backend`, and its bullet in
  `AGENTS.md`.
- **Jira skill.** To remove it, delete `.agents/skills/jira/`, the symlink
  `.claude/skills/jira`, the two `.claude/jira.*example*` files, and its bullet in `AGENTS.md`.
  To use it, copy the example files to `.claude/jira.json` and `.claude/jira.env`, and fill them
  in. Both are in `.gitignore`.
- **PyCharm skill.** Delete `.agents/skills/pycharm-tools/`, its symlink and its bullet in
  `AGENTS.md` if nobody on the project uses PyCharm.
- **mypy hook.** Delete the `mypy` entry in `.githooks.yml` if you do not want type checks on
  every commit. The `[tool.mypy]` settings can stay.
- **Notebooks.** When the first notebook arrives, add an `nbstripout` hook (see
  `docs/LAYOUT.md`).

## Update the template

Projects made from the template do not follow it. To take a later change, add the template as a
remote and compare:

```sh
git remote add template <template-url>
git fetch template
git diff HEAD template/main -- AGENTS.md .agents Makefile .githooks.yml
```

Copy over what you want, and leave what the project changed on purpose.
