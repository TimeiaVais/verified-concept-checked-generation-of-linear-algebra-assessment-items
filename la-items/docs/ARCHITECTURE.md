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
  Depends on `la_items.graph` and `sympy`.
- `la_items.contracts`: the data structures that item families, verification and generation share
  (`ConceptVector`, `ErrorRule`, `Variant`, `Distractor`, `ConceptCheck`). Each one that holds a
  concept id rejects an id not in the graph. Depends on `la_items.graph` and `sympy`.

## Data and flows

1. `concepts.yaml` is loaded once per module that needs it (`steplib.trace`, `contracts`).
2. A reference solver runs inside `recording()`. Each step it calls appends its concept id.
3. `ConceptVector.from_trace()` turns the trace into the derived vector.
4. `ConceptCheck(requested, derived)` accepts the item only when both vectors are equal.

Item families, the verification checks and LLM generation are not built yet.
