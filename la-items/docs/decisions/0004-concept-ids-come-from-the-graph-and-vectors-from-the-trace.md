# ADR-0004: Concept ids come from the graph, and concept vectors from the trace

**Status:** accepted
**Date:** 2026-11-25
**Source:** thesis brief (sections 3 and 5); the contracts commit `3838944`

## Context

The thesis claims that an item's concepts can be determined mechanically from its executed
solution. That claim fails if a concept id can be any string, or if a vector can be typed in or
tagged by an LLM: such a vector cannot be checked. A solution can also call a step whose output it
does not use, which would make the vector too large.

## Decision

- A concept id is an exact `id` from `graph/concepts.yaml`. Every structure that stores one
  (`ConceptVector`, `ErrorRule`, `trace.step`) raises at construction on an unknown id.
- An item's derived concept vector is computed from the trace of its step-library solution, never
  given by hand or by an LLM. A concept counts only if spoiling the output of at least one of its
  step calls changes the answer (the necessity test).
- A family is accepted only if the derived vector equals its target vector exactly.

## Alternatives rejected

- Free-text or LLM tags: not checkable; this is the baseline the thesis compares against.
- Counting every recorded step: an unused call would add a concept the item does not test.
- Accepting a superset of the target: the item would need concepts nobody asked for.

## Consequences

- New concepts enter through the graph file only, and its loader checks them.
- A family whose sampler yields a case where a target concept cannot affect the answer fails the
  concept check; its `find_parameter_problem` must reject that case.
