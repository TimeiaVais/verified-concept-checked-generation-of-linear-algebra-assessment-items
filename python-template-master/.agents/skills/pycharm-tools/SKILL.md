---
name: pycharm-tools
description: Use when mcp__pycharm__* tools are available (PyCharm/JetBrains IDE MCP server). Prefer them over grep/sed/Edit for symbol renames, file diagnostics after edits, finding symbols and callers, running tests or run configurations, formatting, database queries, notebooks and interpreter checks.
---

# PyCharm IDE tools

The IDE exposes `mcp__pycharm__*` tools. They are deferred: load schemas first with
`ToolSearch("select:mcp__pycharm__rename_refactoring,mcp__pycharm__get_file_problems")` (or a
keyword query like `pycharm`). Pass `projectPath` (the working directory) on every call when the
tool accepts it.

## Use the IDE instead of text tools

- Rename a symbol and update all references: `rename_refactoring`, not sed or replace_all.
- Check a file after editing (IDE inspections: errors, warnings, unresolved imports):
  `get_file_problems`; for several files `lint_files`. Do not eyeball it or run the app.
- Find a class, function or field by name: `search_symbol`, not Grep.
- Callers or callees of a function: `analyze_calls`, not Grep for the name.
- Docs or type of the symbol at a position: `get_symbol_info`, not reading the definition.
- Run tests or a configured run target: `get_run_configurations`, then
  `execute_run_configuration`, not an ad-hoc shell command.
- Apply the IDE code style: `reformat_file`.
- Inspect or query a database: `list_database_connections`, `get_database_object_description`,
  `preview_table_data`, `execute_sql_query`, not psql.
- Find which interpreter a file uses: `get_python_environment`, not guessed venv paths.
- Jupyter notebooks: `read_notebook`, `edit_notebook`, `run_notebook_cell`, not raw .ipynb JSON.
- Git status across VCS roots: `git_status`, `get_repositories`.

Keep using the built-in Read/Edit/Grep for plain text lookups and simple edits. The IDE tools win
where semantic knowledge matters.

## Caveats

- `rename_refactoring` misses string references (config, SQL, migrations, docs, reflection). Grep
  for the old name afterwards.
- `execute_terminal_command` asks the user for confirmation unless Brave mode is on. Prefer Bash
  for plain shell work.
- Database tools need the Database plugin and an existing connection. Do not create or edit
  connections without being asked.
- Tools marked router-only are reached through `execute_tool` with a command-line string.
- If a tool errors with an unknown project or stale index, fall back to the built-in tools rather
  than retrying repeatedly.
