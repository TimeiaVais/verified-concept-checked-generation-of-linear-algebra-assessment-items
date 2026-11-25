# ADR-0005: Results and generated families are kept in git

**Status:** accepted
**Date:** 2026-11-25
**Source:** thesis brief (section 9, reproducibility requirements)

## Context

`docs/LAYOUT.md` rule 8 keeps data and artifacts out of git. The thesis brief requires the
opposite for this project: every number in the thesis is produced by a script in `experiments/`
from files in `results/`, and every LLM call is logged with its full prompt and reply. Generated
families are also research data: they show what the model wrote and how many attempts it took. The
files are text and small: JSON Lines logs and short Python modules.

## Decision

- `results/` (experiment outputs and `results/llm_calls/*.jsonl`) and `generated/` (accepted
  families with `generation.json`) are committed to git.
- Prompt templates are files in `src/la_items/generation/prompts/`, never strings in code.
- A file larger than the commit hook's limit (2 MB) goes to external storage and `results/` keeps
  a pointer to it.

## Alternatives rejected

- Keeping results outside git, as LAYOUT rule 8 says: the brief requires the department to
  reproduce the numbers from the repository alone.

## Consequences

- LAYOUT rule 8 does not apply to `results/` and `generated/` in this project.
- Logs may contain the full text of model replies; nothing secret may go into prompts.
