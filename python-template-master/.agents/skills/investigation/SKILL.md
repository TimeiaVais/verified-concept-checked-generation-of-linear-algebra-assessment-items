---
name: investigation
description: Budget file reads and searches when exploring the codebase. Load when the task requires reading multiple files, locating symbols or usages, debugging across modules, or planning a multi-file change.
compatibility: universal
---

# Investigation

## Overview
Use this skill when exploring or debugging the codebase. Not needed for narrow edits where the
target file is already known.

## Read Budget
- Before reading more than 3 files, state the hypothesis you're testing.
- Prefer `grep` over `Read` for "does X exist" or "where is X used" questions.
- Prefer targeted re-reads (`offset`/`limit` around the relevant lines) over full re-reads.

## Re-Reading Files
Don't re-read a file whose contents you already have in context, unless one of these is true:
- You (or a tool) edited it since the last read.
- The user indicated they changed it (e.g., "I just updated X", IDE-opened-file reminders pointing
  at edits).
- Enough turns have passed that the prior Read was likely compacted out of context.
- A failing test, error, or diff implies the on-disk version differs from what you remember.

When unsure whether a file changed, run `git status` or `git diff <path>` before re-reading. It is
cheaper than a full Read.
