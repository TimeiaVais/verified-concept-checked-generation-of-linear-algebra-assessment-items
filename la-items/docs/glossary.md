# Glossary

The project's domain terms. One concept has one word, in code, docs and UI (see "Naming" in
`AGENTS.md` of `python-template-master`). Add a term when a new domain concept appears. Add the
words it replaces under "Retired words". The terms follow Appendix A of the thesis brief.

## Terms

- **item** (завдання): one assessment question with its answer.
- **item family** (сімейство завдань): a program that produces many variants of one item by
  sampling parameters.
- **variant** (варіант): one concrete item produced by a family for a given seed. `Variant`.
- **concept graph** (граф понять): the course's concepts with prerequisite links.
  `la_items/graph/concepts.yaml`.
- **concept id**: the exact `id` of a concept in the concept graph, such as `det_2x2`.
- **block**: one of the four course parts a concept belongs to: `linear_systems`, `matrices`,
  `determinants`, `eigenvalues`.
- **prerequisite**: a concept that must be mastered before another one.
- **concept vector** (вектор понять): the set of graph concepts an item requires.
  `ConceptVector`.
- **step library** (бібліотека кроків), **steplib**: instrumented procedures that record their
  concept when called. `la_items.steplib`.
- **trace** (траса виконання): the list of concept ids of the library steps a solution executed,
  in call order.
- **concept check**: the comparison of the requested concept vector with the derived one.
  `ConceptCheck`.
- **realization** (реалізація): a generated family whose derived concept vector equals the
  requested one.
- **verification pipeline**: the four checks every variant passes, in order: parameter validity,
  independent recomputation, text-program agreement, concept check. `la_items.verification`.
- **reference answer**: the answer computed by a method that shares no code with the step library.
  `compute_reference_answer`.
- **text reader**: a family-specific parser that sees only the rendered question, reads its
  parameters and method, and solves it. `TextReader`.
- **check failure**: the first check a variant failed, as a stage and a reason code.
  `CheckFailure`.
- **necessity test**: rerunning the solution with one step call's output spoiled; the call's
  concept counts only if the answer changes. `verification.pipeline`.
- **static check**: reading generated code with `ast`, before it runs, against the import
  allowlist and the step-library-only rule for `solve`. `generation.static_check`.
- **sandbox**: the child process with a time limit that runs generated code.
  `generation.sandbox`.
- **repair loop** (цикл виправлення): returning a failed family's check failure to the LLM and
  asking again, up to a fixed number of attempts. `generation.loop`.
- **LLM call log**: one JSON line per LLM call with the model, version, parameters, prompt and
  reply. `contracts.LlmCall`.
- **reference set** (еталонний набір): course exercises with concept labels the system did not
  produce. `la_items.reference`.
- **label** (мітка поняття): the hand-written concept vector of one reference exercise part, from
  its textbook section and method. `Exercise.label`.
- **main concept**: the concept a reference exercise's section is about. `Exercise.main_concept`.
- **book erratum**: a printed answer that does not fit the printed exercise; kept and explained.
  `Exercise.book_erratum`.
- **distractor** (дистрактор): a wrong option in a multiple-choice question. `Distractor`.
- **error rule** (правило помилки): a solver with one step replaced by a typical mistake.
  `ErrorRule`.

## Abbreviations

- **slae**: system of linear algebraic equations (СЛАР), in `slae_matrix_form`.
- **det**: determinant, in concept ids such as `det_2x2`.

## Retired words

- `tag`: use **concept id**. A free-text label is not accepted anywhere.
- `malrule`: use **error rule**.
