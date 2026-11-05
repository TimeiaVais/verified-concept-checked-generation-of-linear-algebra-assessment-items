"""Stable data structures shared by item families, verification and generation.

Every concept id stored here is an exact id from the concept graph. A structure
that receives an unknown id raises at construction, so a free-text tag cannot
enter the system.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

import sympy as sp

from graph.loader import load_graph

CONCEPTS = load_graph()


def _check_concept(concept_id: str) -> None:
    if concept_id not in CONCEPTS:
        raise ValueError(f"unknown concept {concept_id!r}")


@dataclass(frozen=True)
class ConceptVector:
    """The set of graph concepts an item requires."""

    concepts: frozenset[str]

    def __post_init__(self) -> None:
        for concept_id in self.concepts:
            _check_concept(concept_id)

    @classmethod
    def from_trace(cls, trace: Iterable[str]) -> "ConceptVector":
        """Derive the vector from the concepts of the executed steps."""
        return cls(frozenset(trace))


@dataclass(frozen=True)
class ErrorRule:
    """A typical mistake: the solver with the step of one concept replaced by a faulty one."""

    name: str
    broken_concept: str

    def __post_init__(self) -> None:
        _check_concept(self.broken_concept)


@dataclass(frozen=True)
class Variant:
    """One concrete item produced by a family for a given seed."""

    seed: int
    parameters: Mapping[str, sp.Basic]
    question_text: str
    answer: sp.Basic

    def __post_init__(self) -> None:
        # sp.Matrix is mutable and not sp.Basic; use sp.ImmutableMatrix.
        for name, parameter in self.parameters.items():
            if not isinstance(parameter, sp.Basic):
                raise TypeError(f"parameter {name!r} is not a SymPy object")
        if not isinstance(self.answer, sp.Basic):
            raise TypeError("answer is not a SymPy object")


@dataclass(frozen=True)
class Distractor:
    """A wrong option: the answer that one error rule produces."""

    answer: sp.Basic
    error_rule: ErrorRule


@dataclass(frozen=True)
class ConceptCheck:
    """Comparison of the requested concept vector with the one derived from the trace."""

    requested: ConceptVector
    derived: ConceptVector

    @property
    def missing(self) -> frozenset[str]:
        """Requested concepts that the solution did not use."""
        return self.requested.concepts - self.derived.concepts

    @property
    def extra(self) -> frozenset[str]:
        """Concepts the solution used but the request did not ask for."""
        return self.derived.concepts - self.requested.concepts

    @property
    def is_accepted(self) -> bool:
        return self.requested == self.derived
