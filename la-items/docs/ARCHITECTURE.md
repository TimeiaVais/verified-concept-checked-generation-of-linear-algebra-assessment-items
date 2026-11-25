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
  `trace.recording()` collects the concepts of the steps called inside it, and
  `trace.perturbing_call()` spoils one call's output for the necessity test. Procedures:
  - `determinants`: `det_2x2`, `minor`, `cofactor_sign`, `cofactor_expansion` (3×3, first row),
    `det_3x3_rule_of_triangles`;
  - `linear_systems`: Gaussian elimination of a 2×2 system (`augmented_matrix`,
    `add_row_multiple`, `forward_elimination_2x2`, `back_substitution_2x2`) and of an n×n system
    with row swaps (`swap_rows`, `forward_elimination`, `back_substitution`);
  - `linear_systems`: Cramer's rule for 2×2 and 3×3 systems (`check_nonsingular`,
    `cramer_rule_2x2`, `cramer_rule_3x3`);
  - `eigenvalues`: eigenvalues of a 2×2 matrix (`subtract_lambda_identity`,
    `characteristic_polynomial_2x2`, `eigenvalues_2x2`) and of a 3×3 matrix with an integer
    eigenvalue (`characteristic_polynomial_3x3`, `eigenvalues_3x3`).

  Depends on `la_items.graph` and `sympy`.
- `la_items.families`: item families, all hand-written. Each one implements
  `contracts.ItemFamily`: `determinants.Determinant3x3CofactorRow1`,
  `linear_systems.Solve2x2LinearSystemGaussian`, `linear_systems.Solve2x2LinearSystemCramer`,
  `eigenvalues.Eigenvalues2x2CharacteristicPolynomial`. Gauss and Cramer solve the same kind of
  system with different concepts, so the question text names the method. Depends on
  `la_items.steplib` and `la_items.contracts`.
- `la_items.verification`: the verification pipeline. `pipeline.verify_variant()` and
  `verify_family()` run the four stages; `parameters` holds stage 1; `necessity` holds the
  necessity test of stage 4; `text_readers` holds the text
  readers for stage 3: one for determinants, one for eigenvalues, and one for 2×2 systems that
  knows the Gauss and the Cramer template. Depends on `la_items.steplib` and
  `la_items.contracts`, not on `la_items.families`, so a reader cannot reuse a family's rendering.
- `la_items.generation`: LLM generation with a repair loop, independent of any provider.
  `llm.LoggedLlmClient` wraps any `contracts.LlmClient` and appends every call to a JSON Lines
  log; `llm.FileReplayClient` replays saved replies. `prompts` reads the templates in
  `generation/prompts/*.md`. `static_check` reads generated code with `ast`; `sandbox` runs it in
  a child process (`sandbox_runner`) with a time limit; `loop.generate_family()` ties them
  together and `save_generated_family()` writes `generated/<family>/`. `targets` lists the targets
  that have an example family and a text reader. Depends on all the modules above.
- `la_items.reference`: the reference set (ADR-0006). `exercises.yaml` holds 29 exercise parts
  from Стороженко 2019 with hand-written labels and the book's answers; `exercises` loads and
  checks them; `solutions` solves each one with library steps; `agreement` compares the answer
  with the book and the derived vector with the label, exactly and by main concept. Depends on
  `la_items.steplib`, `la_items.verification` and `la_items.contracts`.
- `la_items.contracts`: the data structures that item families, verification and generation share
  (`ConceptVector`, `ErrorRule`, `Variant`, `Distractor`, `ConceptCheck`, `CheckFailure`,
  `VerificationReport`, `TextReading`, `LlmResponse`, `LlmCall`) and the `ItemFamily`,
  `TextReader` and `LlmClient` protocols. Each
  structure that holds a concept id rejects an id not in the graph. Depends on `la_items.graph`
  and `sympy`.

## Data and flows

`verify_variant(family, reader, seed)` runs these stages in order and stops at the first failure.
The report holds the failure as a `CheckFailure`: the stage, a reason code from `contracts.Reason`
and a detail with the numbers.

1. **Parameter validity.** The family samples the parameters twice from the same seed; different
   results fail the stage. The pipeline then checks their names
   and shapes against `parameter_shapes`, entries within ±100, and the family's own
   `find_parameter_problem` (degenerate cases, a non-unique answer). Then `solve` runs inside
   `recording()`; a step that raises, a division by zero, or an answer that is not finite, too
   large or too long fails this stage.
2. **Independent recomputation.** `compute_reference_answer` runs inside `recording()` too: it must
   record no steps, and it must give the same answer.
3. **Text-program agreement.** The Ukrainian and the English question are rendered from the same
   parameters. The reader parses each text alone. Both languages must read the same, the text must
   show the program's parameters and the family's method, and the reader's own answer must match.
4. **Concept check.** The necessity test reruns `solve` once per recorded step call, with that
   call's output spoiled by `trace.perturbing_call()`. A concept counts only if spoiling at least
   one of its calls changes the answer. The concepts that count form the derived vector; it must
   equal `target_concepts`.

`generate_family(target, client)` adds two stages before these, for code an LLM wrote:

1. **Static check.** The reply must contain a ```python block with one family class, imports from
   an allowlist only, no file, network or interpreter access, and only step library calls in
   `solve`.
2. **Execution.** The sandbox runs the four stages above on every seed in a child process; a
   timeout or a crash fails this stage. The family must declare the requested target.

The first failure, with its stage, reason, seed and detail, goes into the next prompt, up to
`max_attempts` replies. The accepted family is saved with the model, version, prompt hash and every
attempt; the call log keeps the full prompts and replies.

`concepts.yaml` is loaded once per module that needs it (`steplib.trace`, `contracts`).

`evaluate_reference_set(load_exercises())` runs every exercise's solution inside `recording()`,
applies the necessity test, and returns, per exercise, whether the answer matches the book and how
the derived vector compares with the label.

Not built yet: a real provider client, the LLM tagging baseline, experiments and error rules.
