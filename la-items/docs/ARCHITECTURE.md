# Architecture

How the system works today. Keep it current: update it in the same change that moves a module or
changes a flow (see `.agents/skills/docs/SKILL.md` in `python-template-master`). Why it works this
way is in `docs/decisions/`.

## Overview

A prototype that generates linear algebra assessment items for four blocks: linear systems,
matrices, determinants and eigenvalues. Each item comes from an item family, a program that is
checked before anyone sees it. The concept vector of an item is derived from the steps its
reference solver executed, not from a tag. The users are the course teachers and the thesis.

## Modules

- `la_items.graph`: the concept graph. `concepts.yaml` holds the concepts and their prerequisites;
  `loader.load_graph()` reads it and rejects duplicates, unknown blocks, unknown prerequisites and
  cycles. Depends on `pyyaml` only.
- `la_items.steplib`: the step library. `trace.step(concept_id)` binds a step to one graph concept;
  `trace.recording()` collects the concepts of the steps called inside it. `determinants` holds
  the steps `det_2x2`, `minor`, `cofactor_sign` and `cofactor_expansion` (3×3, first row).
  `linear_systems` holds the Gaussian elimination steps for a 2×2 system. Depends on
  `la_items.graph` and `sympy`.
- `la_items.families`: item families. Each one implements `contracts.ItemFamily`.
  `determinants.Determinant3x3CofactorRow1` and `linear_systems.Solve2x2LinearSystemGaussian` are
  hand-written. Depends on `la_items.steplib` and `la_items.contracts`.
- `la_items.verification`: the verification pipeline. `pipeline.verify_variant()` and
  `verify_family()` run the four stages; `parameters` holds stage 1; `text_readers` holds one text
  reader per family for stage 3. Depends on `la_items.steplib` and `la_items.contracts`, not on
  `la_items.families`, so a reader cannot reuse a family's rendering.
- `la_items.contracts`: the data structures that item families, verification and generation share
  (`ConceptVector`, `ErrorRule`, `Variant`, `Distractor`, `ConceptCheck`, `CheckFailure`,
  `VerificationReport`, `TextReading`) and the `ItemFamily` and `TextReader` protocols. Each
  structure that holds a concept id rejects an id not in the graph. Depends on `la_items.graph`
  and `sympy`.

## Data and flows

`verify_variant(family, reader, seed)` runs these stages in order and stops at the first failure.
The report holds the failure as a `CheckFailure`: the stage, a reason code from `contracts.Reason`
and a detail with the numbers.

1. **Parameter validity.** The family samples the parameters once. The pipeline checks their names
   and shapes against `parameter_shapes`, entries within ±100, and the family's own
   `find_parameter_problem` (degenerate cases, a non-unique answer). Then `solve` runs inside
   `recording()`; a step that raises, a division by zero, or an answer that is not finite, too
   large or too long fails this stage.
2. **Independent recomputation.** `compute_reference_answer` runs inside `recording()` too: it must
   record no steps, and it must give the same answer.
3. **Text-program agreement.** The Ukrainian and the English question are rendered from the same
   parameters. The reader parses each text alone. Both languages must read the same, the text must
   show the program's parameters and the family's method, and the reader's own answer must match.
4. **Concept check.** `ConceptVector.from_trace()` turns the trace of stage 1 into the derived
   vector; it must equal `target_concepts`.

`concepts.yaml` is loaded once per module that needs it (`steplib.trace`, `contracts`).

Error rules and LLM generation are not built yet.
