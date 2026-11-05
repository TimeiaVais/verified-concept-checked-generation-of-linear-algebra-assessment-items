---
name: docs
description: Read and maintain the project's docs and architectural decision records (ADRs). Load before planning a feature or a design change, when a decision that outlives the task is made, when a phase or feature finishes, and when moving or renaming a doc.
compatibility: universal
---

# Docs

## Where things live

- `docs/LAYOUT.md`: how the repository and the package are organized. Kept current.
- `docs/ARCHITECTURE.md`: how the system works today. Kept current.
- `docs/glossary.md`: the project's domain terms and the words retired for them. Add a term when a
  new domain concept appears. Kept current.
- `docs/decisions/NNNN-slug.md`: why it works that way, one ADR per decision. Permanent and
  append-only.
- `docs/backlog/`: proposals and handoffs not started or partly done, for issues with several
  facets that need brainstorming. A problem that fits one ticket goes to the tracker, not here.
  Lives until done.
- `docs/done/`: finished handoffs and tickets, how it was built. History, not updated.
- `docs/reference/` (optional): external material and dated snapshots. Kept as is.
- Runbooks and the plan, `docs/RUN.md` and `docs/ROADMAP.md` (optional, create when needed): kept
  current.

File names in `backlog/` and `done/`: `YYYY-MM-DD-NAME.md` (or `.html`), so a listing sorts in
chronological order. The date is the day the doc was created, and it stays the same when the doc
moves to `done/`. `NAME` keeps the type prefix: `2026-10-21-HANDOFF_TRAIN_JOB.md`,
`2026-10-21-PROPOSAL_DATA_LAYER.md`. No running number: two branches would take the same one.

Tickets: a problem that can be written as a single ticket goes to the tracker directly, not into
`docs/backlog/`. `backlog/` is for complex, multi-faceted issues that need brainstorming before
they can be split into tickets.

Where a detail goes:
- About one spot in the code → a code comment there.
- A rule or invariant that spans modules, or a choice a future change could undo without knowing
  why → an ADR.
- A temporary state (what is built, what is open) → the doc's status line.
- What git log or the code already says → nowhere.

## Grounding: before planning

1. `ls docs/decisions/` and read the ADRs whose titles touch the area you change.
2. Name them in the plan ("follows ADR-0007").
3. If the plan contradicts an accepted ADR, say so and ask. Do not work around it. If the ADR is
   wrong, propose one that supersedes it.
4. `docs/backlog/` may already hold a proposal or handoff for the task, and the tracker a ticket.
   Read them before designing.

## ADRs

Template: `docs/decisions/TEMPLATE.md`. Number = next free four-digit number. Keep one under ~40
lines.

- **Propose first, never write silently.** When a decision worth an ADR comes up, put the draft
  (title, decision, rejected alternatives) in your reply and ask. Write the file only after the user
  agrees.
- **The bar:** would a plausible future change undo this without knowing why it was made? If not,
  no ADR. Library choices made for convenience, naming, and one-module details do not qualify.
- **State the decision plainly.** No "for now" or "may change". Put the reason this option was
  chosen in Context (including "the default; nothing yet argues for another"): that reason is what
  a later ADR argues against.
- **Ids are stable; paths are not.** Code comments may cite `ADR-NNNN`, but only once that ADR is
  committed (`git ls-files docs/decisions`). Before that, make the comment self-contained. The same
  holds for every doc a comment points at: never cite an untracked file.
- Cite the source: the handoff, ticket or commit where the decision was made.

## Changing a decision

Accepted ADRs are append-only: the body is never edited. The only line that changes is
`**Status:**`, and only to point at the ADR that changed it. A change is always a new ADR, proposed
first like any other.

- Replaced whole: the new ADR says `Supersedes: ADR-NNNN`. The old status becomes
  `superseded by ADR-MMMM`.
- One part changed or narrowed: the new ADR says `Amends: ADR-NNNN` and names the part (a rule, a
  case, a threshold). The old status becomes `accepted, amended by ADR-MMMM`.
- No longer applies (feature removed): the new ADR says `Retires: ADR-NNNN` and why. The old
  status becomes `retired by ADR-MMMM`.

- An amended ADR stays in force except for the part the amending ADR names. Read the chain from the
  oldest.
- The new ADR's Context says what changed since the old one: new evidence, a new requirement, an
  incident.
- Example: an ADR says rows with a missing label are skipped and counted. Later, a missing label
  counts as data corruption. A new ADR `Amends:` it: "fail the job when more than X% of the rows
  have no label; below that, skip and count as before". The old ADR's status becomes
  `accepted, amended by ADR-<new>`.
- Before writing the new ADR, `grep -rn 'ADR-NNNN' src tests docs`. Code and docs whose rule
  changed should cite the new ADR; those that rely on the unchanged part keep the old one.
- When reading ADRs for grounding, read the status line first and follow `superseded by` /
  `amended by` to the current rule.

## Status lines

Every doc in `backlog/` and `done/` carries one, right under the title block:

- backlog: `**Status (YYYY-MM-DD):** not started.` |
  `partial. Built: <what> (<commit>). Open: <what>.` | `blocked by <doc or ADR>.`
- done: `**Done:** <commit or merge commit>.` Keep the original status after it as
  `Status at handoff (date): …` instead of deleting it.

Update the status line in the same change that changes the state: when a phase is committed, not
later.

## Closing: moving a doc from `backlog/` to `done/`

1. Status line → `**Done:** <commit>`.
2. Go through its decisions (the D-items in handoffs). Propose an ADR for each one that passes the
   bar.
3. If modules or flows changed, update `docs/ARCHITECTURE.md`.
4. Work left over (checks, follow-ups) → a tracker ticket, linked from the status line. A follow-up
   that needs brainstorming → a new proposal in `backlog/`.
5. Move with `git mv`, keeping the file name (date included), then fix links (below).

## Moving or renaming a doc

Relative links break, and so do paths written in backticks. Find both:

```sh
grep -rn '<old file name>' docs README.md AGENTS.md .agents src tests \
  --include='*.md' --include='*.html' --include='*.py'
```

Fix live docs (backlog, ARCHITECTURE, runbooks, code). In `done/` docs, fix links and paths, but
leave prose that records what was reviewed at the time. In ADRs, fix the path in the `**Source:**`
line: it is a link, not part of the decision, so the append-only rule does not cover it.

## Writing

- Short and plain. One idea per bullet. Facts with paths and commits, not adjectives.
- A working doc names its date and branch.
- Keep lines to 100 characters.
- Do not duplicate: link to the ADR or doc that already says it.
