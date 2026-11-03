# AGENTS.md

This guide gives repository-specific instructions for agents that change code here.

## Build, Test, and Development Commands

Check for `Makefile.local` to look for customized local env setup.

- `make bootstrap`: install the project dependencies and the git hooks.
- `make test`: run project tests.
- `make lint`: inspect project source code for problems and errors.
- `make build`: build project packages.
- `make clean`: clean up the project environment and build artifacts.

## Agent-Specific Instructions

- When changing Python code, follow `.agents/skills/python/SKILL.md`.
  The layout of the repository and of the package is in `docs/LAYOUT.md`.
- When investigating the codebase (multi-file reads, locating symbols, debugging across modules),
  follow `.agents/skills/investigation/SKILL.md`.
- When building an API service with a database (endpoints, tables, migrations), follow
  `.agents/skills/api-backend/SKILL.md`. Skip it otherwise.
- When reading or writing Jira issues, or planning work as Jira tasks, follow
  `.agents/skills/jira/SKILL.md`.
- When `mcp__pycharm__*` tools are available (PyCharm MCP server), follow
  `.agents/skills/pycharm-tools/SKILL.md`. Skip it otherwise.
- Before planning a feature or design change, when a decision that outlives the task is made, when a
  phase finishes, or when moving a doc, follow `.agents/skills/docs/SKILL.md`.
  Accepted decisions are in `docs/decisions/`.

## Honesty and Critical Thinking

- Don't open with praise or agreement. Start with the substance.
- Don't praise user observations ("Good catch", "Great point", "Exactly right"). Acknowledge
  corrections neutrally and move on.
- If something is wrong, say so. Don't soften a correct assessment.
- Evaluate proposals on merit before implementing, not after. If the user's proposal is best, say
  why; if not, say what is and why.
- Hold a correct position under pushback unless given new evidence or argument.
- If a request contradicts an established pattern, name the contradiction before implementing.
- If a refactor worsens a concrete metric (indirection, testability, coupling), say so and propose
  an alternative.
- Never silently implement a request you disagree with. State the concern, then ask whether to
  proceed.
- For ambiguous requests, present 2–3 concrete interpretations with tradeoffs instead of picking
  silently.
- If the stated goal and proposed solution conflict, address the goal.
- If a prior decision turns out wrong, say so directly rather than working around it.

## Architecture First

- Before implementing, decide where the change belongs in the system: which module, layer and data
  format, and why it fits there. State this in the plan.
- Before reusing an existing structure (a module, a shared data file, a generic dict or JSON blob),
  check what it was built for. If the new data or behaviour differs from that (other owner,
  lifecycle, mutability, or other parts depend on it), say so and ask before doing it. Fitting
  something in because it is convenient is a design decision, not an implementation detail.
- Warning signs: a special case added for the new thing, code parsing data it was meant to treat as
  opaque, references nothing enforces, write-once data in a mutable store, a second copy kept in
  sync by hand.
- If the right design is bigger than the task, present both options with tradeoffs. Do not pick the
  convenient one silently.

## Naming

A name makes code clear or opaque. This holds for every name: variables, functions, classes,
modules, files, dict and JSON keys, schemas, config keys, env vars. Rules in the skills for one kind
of name refine these rules and do not override them.

- A name tells a reader who has not seen the code what the thing is, in domain terms. Test: cover
  the definition. Can the reader guess what it holds or does?
- A name stays correct when a sibling appears. Test: if a second kind of X is added, is this name
  still unambiguous? (`run` became `workflow_run`, `sample` became `sourced_retailer_image`.)
- One concept, one word, in every layer (code, API, UI, docs). One word never means two things. Use
  the terms in `docs/glossary.md`; when a new domain term appears, add it there.
- Do not name a thing by how it works, by its history or by its position: `new_`, `old_`, `tmp`,
  `v2`, `step1`, `pool`, `manager`, `handler`, `utils`, `helpers`, `common`, `misc`.
- Do not use these words alone: `data`, `info`, `item`, `obj`, `thing`, `value`, `result`,
  `process`. Add what the thing is (`prediction_result`, `release_number`).
- Form by kind: a module or file is a noun for what it contains; a class is a noun; a function is a
  verb and its object; a boolean starts with `is_` or `has_`; a collection is plural; a dict or JSON
  key is the name its field would have; a unit goes in the name (`timeout_seconds`).
- Length grows with scope. An abbreviation is allowed only if it is in the glossary.
- The more places a name is visible, the more it costs to change. In order: stored field or column,
  public API field or schema, file or module, class, function, local. For the first three, state in
  the plan why the name is right. If it introduces a new domain concept, wait for the user's
  decision.
- When you rename, rename everywhere in the same change. Leave no alias and no old name. A module
  name must not shadow a library.

## Simplicity

- No abstractions for single-use code.
- No error handling for impossible scenarios.
- No "flexibility" or "configurability" that wasn't requested.
- If you write 200 lines and it could be 50, rewrite it.
- Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## Surgical Changes

- Don't improve adjacent code, comments, or formatting. Touch only what the task requires.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it. Don't delete it.
- Remove imports, variables and functions that *your* changes made unused. Leave pre-existing dead
  code alone unless asked.
- Test: every changed line should trace directly to the user's request.

## Goal-Driven Execution

- Before starting a multi-step task, state a brief plan with explicit verification per step:
  ```
  1. [Step] → verify: [check]
  2. [Step] → verify: [check]
  ```
- Convert vague tasks into verifiable success criteria before implementing ("fix the bug" → "write
  a test that reproduces it, then make it pass").
- Strong success criteria enable independent looping. Weak criteria ("make it work") require
  constant clarification. Resolve them upfront.
- Before writing any code or running any commands, get explicit confirmation from the user.
    - Present the plan and wait. Do not proceed until the user replies with approval.
    - "Seems reasonable" or silence is not approval. Ask: "Shall I proceed?" and wait for a clear
      yes.
    - If the request is exploratory (read-only analysis, explaining code, answering a question),
      skip this gate.

## Output Shape

- No preamble, no recap of the diff, no trailing "Summary" sections by default.
- Cite code as `path:line`, not pasted blocks.
- Lead with the answer. Skip restating the question.
- Add a brief summary only when the response covers substantial ground (multi-file changes,
  multi-step investigation, several findings) and a recap genuinely aids navigation. For narrow
  tasks, skip it.
- When you explain something to me (answers, summaries, explanations of files or code), write 80% of
  the way to ASD-STE100 Simplified Technical English: one idea per sentence, short sentences, active
  voice, one word for one meaning. Keep product names, code names and domain terms as they are. Do
  not replace them with simpler words.
- Keep lines in files you write to 100 characters or fewer. Tables and code blocks may exceed it
  when they cannot be wrapped.

## Git Commit Messages

- Subject line: 50–72 characters, imperative mood (e.g. "Add X", "Fix Y", "Remove Z").
- Body: omit unless the *why* is non-obvious from the diff. Never summarise what changed. The diff
  does that.
- Keep bullet lists and multi-paragraph descriptions for PR descriptions, not commits.
- Do not mention LLM or AI agent involvement (no "Co-Authored-By: Claude", no "Generated by", etc.).
