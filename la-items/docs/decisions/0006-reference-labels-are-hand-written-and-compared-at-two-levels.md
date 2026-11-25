# ADR-0006: Reference labels are hand-written and compared at two levels

**Status:** accepted
**Date:** 2026-11-25
**Source:** thesis brief (section 7, reference sets; section 10, solution paths are not unique)

## Context

The main claim is tested by comparing trace-derived concept vectors with labels the system did
not produce. The brief takes those labels from course exercises: the section an exercise sits in
gives its concepts. Section labels are coarse, a solution path is not unique (a 3×3 determinant
can be expanded or computed by the rule of triangles), and many exercises ask for two things at
once (the matrix method and Cramer's rule; eigenvalues and eigenvectors).

## Decision

- Labels live in `src/la_items/reference/exercises.yaml` and are written by hand from the
  textbook section and the method the exercise names. Where it names none, the label follows the
  method the book itself uses for that topic, and the file says which page shows it. A label is
  never derived from a trace.
- One entry is one part of one exercise; the entry's `task` names the part, and the label covers
  that part only.
- The encoded solution follows the same method as the label.
- Agreement is reported at two levels: the exact vector, and whether the section's main concept
  is in the derived vector.
- The book's printed answer is checked too. An answer that does not fit the printed exercise is
  kept and explained in `book_erratum`, not corrected.

## Alternatives rejected

- Labels from the trace or from an LLM: the comparison would test the system against itself.
- One label per whole exercise: half of the label would have no encoded solution.
- Only exact agreement: it hides whether a disagreement is about the main concept or about a
  detail the section label cannot express.

## Consequences

- Disagreements stay visible and are a result. Example: in 2.45 and 2.47 the necessity test drops
  `cofactor_sign`, because zero minors make the signs irrelevant, while the label lists it.
- Adding an exercise needs a solution in `reference/solutions.py` built from library steps only.
