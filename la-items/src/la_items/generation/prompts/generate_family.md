You write one item family for a linear algebra assessment system. An item family is a Python
module that samples parameters from a seed, renders the question in Ukrainian and English, and
solves it. Every family is checked automatically before it is accepted.

## Target concepts

The solution must use exactly these concepts from the course concept graph, no more and no less:

$target_concepts

## Step library

A solution may compute only by calling these steps. Each call records its concept, and the set of
recorded concepts whose output the answer needs must equal the target.

$step_library

## Interface

Write exactly one class with these class attributes and methods:

- `name: str`, a short snake_case name of the family.
- `target_concepts = contracts.ConceptVector(frozenset({...}))` with the target concepts above.
- `parameter_shapes: dict[str, tuple[int, int]]`, the shape of every parameter matrix.
- `sample_parameters(self, seed: int) -> dict[str, sympy.Basic]`: create
  `rng = random.Random(seed)` and use only `rng` for randomness. Keep entries between -5 and 5.
  Matrices must be `sympy.ImmutableMatrix`. Resample until `find_parameter_problem` returns None.
- `find_parameter_problem(self, parameters) -> contracts.ParameterProblem | None`: return
  `contracts.ParameterProblem("degenerate_parameters", "...")` or
  `contracts.ParameterProblem("answer_not_unique", "...")` for a case where the method would not
  apply, the answer would not be unique, or a target concept would not affect the answer.
- `render_question(self, parameters, language) -> str`: `language` is "uk" or "en". Build both
  languages from the same parameters.
- `solve(self, parameters) -> sympy.Basic`: call step library functions only. No arithmetic
  operators, no SymPy functions or methods, no other calls.
- `compute_reference_answer(self, parameters) -> sympy.Basic`: compute the same answer
  independently with SymPy. Never call the step library here.

## Rules

- Import only: `random`, `typing`, `collections.abc`, `sympy`, `from la_items import contracts`,
  and the step library modules listed above, as `from la_items.steplib import <module>`.
- Do not use `open`, `exec`, `eval`, `__import__`, or names that start with two underscores.
- Render the question with exactly this sentence form, so that an independent reader can parse it.
  Only the numbers change between variants:

$text_templates

## Previous attempt

$feedback

Reply with the whole module in one fenced block that starts with ```python.
