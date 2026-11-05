---
name: python
description: Develop or refactor the codebase.
compatibility: universal
---

# Python

## Overview
Use this skill for Python changes in the repository. Where files and packages go is in
`docs/LAYOUT.md`.

## Agent Interface
- Display name: Python
- Short description: Python develop and refactor guide
- Default prompt: Follow conventions, keep correctness first, optimize for speed when safe, and run
  `make test` if asked.

## Conventions
- Prefer Python 3.11+ features (the floor is `requires-python` in `pyproject.toml`) and pragmatic
  performance improvements only when correctness is preserved.
- Prefer memory-efficient approaches and avoid heavy allocations when possible.
- Use numeric separators for large integer literals when it improves readability.
- Deliver architecture-level solutions with clear tradeoffs and assumptions.
- Keep a peer-to-peer tone and assume deep experience.
- Prefer composition over subclassing. Subclass only to implement an abstract base class, or where
  there is no other way: the framework requires it (`pydantic.BaseModel`, `Exception`). In every
  other case, compose (hold the other object as a field), or state a strong justification for the
  subclass in a comment next to it. Extending a model with extra fields (`class Credentials(User)`)
  is composition: `user: User` plus the extra fields.

## Code Style and Formatting
- Use Python best practices and project patterns, favoring clarity, correctness, and
  maintainability over cleverness.
- Respect `.editorconfig`: 4-space indent, LF, trim trailing whitespace, final newline.
- Keep line length to 100 for `.py` (the `black` setting in `pyproject.toml`).
- Always run `black` and `isort` (profile: `black`) on touched files.
- Type-annotate all defs and prefer PEP 604 unions (`str | os.PathLike`) and builtin generics
  (`list[str]`). When a union mixes `msgspec.Struct` with a forward reference string, use
  `typing.Union[...]`.
- Import modules, not names: `import typing`, `import collections.abc`, `import pydantic`, then
  `typing.Final`, `pydantic.BaseModel`. Do not write `from typing import ...` or
  `from pydantic import ...`.
- Group imports as stdlib, third-party, then local, and keep them sorted.
- Use absolute imports (`from my_package import module`), never relative imports.
- Exposed public API modules should define `__all__` near the top.
- Use NumPy-style docstrings and `name : type` entries for `Parameters`, `Returns`, `Yields`,
  `Raises`, and `Notes`.
- Write docstrings and doctest-style explanatory prose in grammatically correct English. When
  describing a function or method as the subject, treat it as `it` and use the matching verb form
  (for example, `it goes`, `it returns`, `it raises`).
- For logger calls (loguru), use f-strings and prefer `!r` for values (`f"... {value!r}"`; plain
  `{}` only for type names and numbers). Do not pass formatting arguments to the logger.
- Keep module constants explicit with `typing.Final` where appropriate.
- Prefer `@dataclasses.dataclass(..., slots=True)` and use `frozen=True` for immutable data holders.
- Name a function or a method with a verb and its object (`create_invoice`, `list_active_users`,
  `read_config_file`), not a bare verb or noun (`create`, `update`, `get`, `items`, `file`). The
  name must be clear without its module or class around it: in a stack trace, a log line or a grep
  result. A short name is fine only for a private helper used a few lines away.
- Place private helpers (for example `_func`) near the functions that use them.
- Avoid local aliases of object attributes (for example `var = self.obj.var`) when direct access is
  clearer.
- Don't use `global` or `nonlocal`. Use nested functions only in rare cases.
- Implement functions and methods with a single return statement: assign the value to a variable
  named for what it holds and return it at the end. Take the name from the function's object:
  `invoice` in `create_invoice`, `active_users` in `list_active_users`; a predicate for a bool
  (`is_valid`). Do not use bare `result`, and do not shadow a parameter or an imported module.
  Initialize the variable at the top only when the body builds it up step by step; when it is one
  expression, assign it once right before the return. Replace early returns with `if`/`else`
  branches that each assign it. Functions that already use `result` stay as they are until you
  touch them.
- A `return` statement returns only names, never an expression: no calls, operators, literals built
  in place, comprehensions or attribute access (`return invoice`, `return first, second`). Do every
  operation before it and assign the value to a variable. This holds for one-line helpers and
  properties too.
- Separate logical blocks inside a function body with one blank line: setup statements, each loop,
  each `if`/`elif`/`else` chain, and the final result assembly. Put a blank line before the final
  `return` whenever the body has more than one block. Do not put blank lines right after a
  docstring or right after a block opener (`for ...:`, `if ...:`).
  Spacing is generous; the blank lines are what make the steps of a function readable at a glance:
  - A compound statement (`if`, `for`, `while`, `with`, `try`) gets a blank line before it when
    statements precede it, and after it when statements follow it, at every nesting level. Two `if`
    chains in a row are two blocks: a blank line between them.
  - In a `try`, put a blank line before each `except`, `else` and `finally` clause.
  - A statement that is a step of its own, such as a blocking wait (`event.wait()`), a cleanup call
    (`logger.remove(sink)`) or a phase's opening or closing log line, gets blank lines on both
    sides.
  - The exception is a one-line guard that only raises (`if x is None: raise ...`): it stays
    attached to the statement it protects.

  ```python
  logger.info(f"claimed by {self.node_id} (attempt {job.attempt})")

  started = time.monotonic()
  stats = timing.track()

  try:
      stage = self.stages.get(job.type)
      if stage is None:
          raise LookupError(f"no stage for job type {job.type!r} on this node")
      stage(job)
      status = "succeeded"

  except jobs.Cancelled:
      status = "cancelled"

  except Exception:
      status = "failed"

  logger.info(f"{status} in {time.monotonic() - started:.0f} s")
  ```
- When a statement exceeds the line length, break it rather than relying on long lines:
  - wrap a long right-hand side in parentheses (`x = (\n    a / b\n)`), never with backslashes;
  - split a long signature or call so that its arguments move to their own lines; if they still do
    not fit on one line, put one argument per line with a trailing comma;
  - break long comprehensions and inline collections across lines inside their own brackets.
  The trailing comma keeps `black` from collapsing a deliberately exploded call back onto one line.
