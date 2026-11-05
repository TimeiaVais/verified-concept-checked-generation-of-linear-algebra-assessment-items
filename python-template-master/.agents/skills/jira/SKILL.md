---
name: jira
description: Read and write Jira Cloud issues for the current project, and write good feature tasks. Load when the user mentions Jira, a ticket or issue key (ABC-123), an epic, or asks to create, update, comment on, move or link tasks, or to plan work as Jira tasks.
compatibility: universal
---

# Jira

Optional skill. Delete it, and its line in `AGENTS.md`, if the project does not use Jira.

## Setup

The client is `jira.py` next to this file (standard library only). From the repository root:
`python3 .agents/skills/jira/jira.py -h`.

It needs a per-project config, `.claude/jira.json`, found by walking up from the current directory.
It holds what changes per project (epic, project key, conventions); this file holds what does not.
Copy `.claude/jira.example.json` to `.claude/jira.json` and fill it in.

```json
{
  "site": "example.atlassian.net",
  "cloud_id": "<from https://example.atlassian.net/_edge/tenant_info>",
  "email": "<the Atlassian account email>",
  "env_file": ".claude/jira.env",
  "token_env": "ATLASSIAN_TOKEN",
  "project": "ABC",
  "epic": "ABC-100",
  "issue_type": "Task",
  "assign_to_self": true,
  "branch": "ABC-NNNN-<summary slug>",
  "notes": ["project-specific facts the agent must know"]
}
```

- Read `notes` and `branch` before acting; they override the defaults below.
- `.claude/jira.json` and `.claude/jira.env` hold a personal email and a token. Both are in
  `.gitignore`. Keep them out of git.
- No config yet: ask for site, project, epic and the token's location, fetch the cloud id, write
  the file, then run `whoami` and `children` to check.

### Token

- An API token from id.atlassian.com → Security → API tokens, in the env file the config names, as
  one line `ATLASSIAN_TOKEN=<token>` (see `.claude/jira.env.example`). Never print it. Keep it out
  of an app's `.env`: a settings loader that forbids unknown keys fails on it (and may echo it).
- Scopes for a scoped token: `read:jira-work`, `write:jira-work`, `read:jira-user`, `read:me`.
  Nothing that manages projects or webhooks.
- Scoped tokens work only through `https://api.atlassian.com/ex/jira/<cloud_id>`, not the site URL;
  `jira.py` always uses the gateway. Basic auth: `email:token`.
- Calling the API by hand in zsh: pass `-u "$EMAIL:$TOKEN"` inline. An unquoted `$VAR` holding
  `-u …` is not split by zsh, and every call returns 401.
- The client uses REST API v2, so descriptions and comments are Jira wiki markup strings (below),
  not ADF JSON.

## Rules

- **Every write is outward-facing.** Show the full draft (summary, type, parent, description) and
  get the user's OK before `create`, `edit`, `comment`, `attach`, `transition` or `link`. Approval
  for one set of writes does not cover the next. Before `attach`, name the files and read them: a
  file can hold ids, emails or secrets.
- Use `create --dry-run` to show the exact payload when the user wants to see it.
- Never delete an issue. To drop one, propose the Cancel transition.
- Read before writing: `children` to see siblings and their style, `get` before editing a
  description.
- Write the body to a temp file and pass `--body-file`; remove the file after.
- `attach KEY FILE [FILE ...]` uploads files as attachments (Jira's limit is 10 MB per file by
  default). Put short text that people read in a comment or the description; attach what they
  download (SQL, logs, exports).
- After writing, report the key and the URL `https://<site>/browse/<KEY>`.

## Workflow for planned work

1. Plan with the user first. One task per phase or reviewable change, not per file.
2. Create the tasks under the epic after approval. Express order with `link A blocks B`.
3. Starting a task: `transition KEY 'In Progress'`, branch named by the config's `branch` pattern.
4. Phase ready for review: a comment saying what was done and what was not checked (below). The
   user commits and closes the task unless they ask otherwise.
5. Decisions made during the work go back into the description (a "Decisions" section), not only
   into comments.

## Writing a feature task

### Summary

- Starts with a verb and names the outcome: "Retry failed export jobs", "Add type hints to the
  loader module".
- Readable in a list without opening the ticket. Under ~80 characters. No stacked `[Tag] [Tag]`
  prefixes; the epic already groups the work.
- Match the style of the epic's existing tasks.

### Description template

```
h3. Why
What is wrong or missing today, and what it costs. Concrete: file paths, counts, user-visible
behaviour.

h3. What
The change, as outcomes and the parts it touches (modules, config, data, migration). Enough that a
reviewer can tell scope; not a step-by-step implementation plan.

h3. Acceptance criteria
* Binary, testable statements. Each one passes or fails; no "works well".
* Cover the failure paths and edge cases, not only the happy path.
* Name how it is checked: a test, a dry run, a check on a staging copy.

h3. Out of scope
* What a reader might expect here but is deliberately left out, with the task or doc that covers it.

h3. Depends on
* Other tasks (also as Jira links) and why.

h3. Links
* Design doc, ADR, merge request.
```

Drop a section that would be empty. Keep the whole description short enough to read in a minute;
put long design material in a linked doc instead of pasting it.

### Quality checks before showing a draft

- **Independent and small (INVEST).** Deliverable and reviewable on its own; if it needs another
  task's code, say so in "Depends on". Too large to review in one sitting → split by outcome, never
  by layer-of-the-day.
- **Criteria are outcomes, not steps.** "A deleted account no longer appears in the account list",
  not "add a WHERE clause".
- **No ambiguity.** Numbers instead of "fast" or "large". Each acceptance criterion has one
  reading.
- **Facts, not adjectives.** Paths, names, counts, commits.
- **Risks named.** Data that could be lost, deploy ordering, changes that cannot be undone.
- **Links point at committed docs** that others can open, not local files.

### Comments

- Say what was done and what was not, with the commit or MR: "The export job retries 3 times;
  tested on a copy of staging. Not checked under load." Not "ready for review".

## Jira wiki markup (v2)

- Heading: `h3. Title`
- Bullet, nested: `* item`, `** item`
- Numbered: `# item`
- Bold, italic: `*bold*`, `_italic_`
- Inline code: `{{code}}`
- Code block: `{code:python}` … `{code}` (or `{noformat}` … `{noformat}`)
- Link: `[text|https://…]`
- Table: `||head||head||` on the first row, then `|cell|cell|`

Markdown (`**`, backticks, `#` headings) is not rendered; convert it.
