"""Stable data structures shared by item families, verification and generation.

Every concept id stored here is an exact id from the concept graph. A structure
that receives an unknown id raises at construction, so a free-text tag cannot
enter the system.
"""

import collections.abc
import dataclasses
import typing

import sympy

from la_items.graph import loader

__all__ = [
    "CONCEPTS",
    "CheckFailure",
    "ConceptCheck",
    "ConceptVector",
    "Distractor",
    "ErrorRule",
    "ItemFamily",
    "Language",
    "ParameterProblem",
    "ParameterReason",
    "Reason",
    "Stage",
    "TextReader",
    "TextReading",
    "Variant",
    "VerificationReport",
]

CONCEPTS: typing.Final = loader.load_graph()

Language = typing.Literal["uk", "en"]

# The verification stages, in the order the pipeline runs them.
Stage = typing.Literal[
    "parameter_validity",
    "independent_recomputation",
    "text_program_agreement",
    "concept_check",
]
ParameterReason = typing.Literal["degenerate_parameters", "answer_not_unique"]
Reason = (
    ParameterReason
    | typing.Literal[
        "wrong_shape",
        "number_too_large",
        "division_by_zero",
        "expression_too_large",
        "reference_mismatch",
        "reference_uses_step_library",
        "text_unreadable",
        "text_parameters_mismatch",
        "text_method_mismatch",
        "language_mismatch",
        "text_answer_mismatch",
        "concept_mismatch",
    ]
)


def _check_concept(concept_id: str) -> None:
    if concept_id not in CONCEPTS:
        raise ValueError(f"unknown concept {concept_id!r}")


@dataclasses.dataclass(frozen=True, slots=True)
class ConceptVector:
    """The set of graph concepts an item requires.

    Raises
    ------
    ValueError
        It raises when a concept is not in the graph.
    """

    concepts: frozenset[str]

    def __post_init__(self) -> None:
        for concept_id in self.concepts:
            _check_concept(concept_id)

    @classmethod
    def from_trace(cls, trace: collections.abc.Iterable[str]) -> "ConceptVector":
        """Derive the vector from the concepts of the executed steps.

        Parameters
        ----------
        trace : Iterable[str]
            The concepts recorded by `la_items.steplib.trace.recording`, in call order.

        Returns
        -------
        ConceptVector
            The set of distinct concepts in the trace.
        """
        concept_vector = cls(frozenset(trace))

        return concept_vector


@dataclasses.dataclass(frozen=True, slots=True)
class ErrorRule:
    """A typical mistake: the solver with the step of one concept replaced by a faulty one.

    Raises
    ------
    ValueError
        It raises when `broken_concept` is not in the graph.
    """

    name: str
    broken_concept: str

    def __post_init__(self) -> None:
        _check_concept(self.broken_concept)


@dataclasses.dataclass(frozen=True, slots=True)
class Variant:
    """One concrete item produced by a family for a given seed.

    Raises
    ------
    TypeError
        It raises when a parameter or the answer is not a SymPy object.
    """

    seed: int
    parameters: collections.abc.Mapping[str, sympy.Basic]
    question_uk: str
    question_en: str
    answer: sympy.Basic

    def __post_init__(self) -> None:
        # sympy.Matrix is mutable and not sympy.Basic; use sympy.ImmutableMatrix.
        for name, parameter in self.parameters.items():
            if not isinstance(parameter, sympy.Basic):
                raise TypeError(f"parameter {name!r} is not a SymPy object")

        if not isinstance(self.answer, sympy.Basic):
            raise TypeError("answer is not a SymPy object")


@dataclasses.dataclass(frozen=True, slots=True)
class Distractor:
    """A wrong option: the answer that one error rule produces."""

    answer: sympy.Basic
    error_rule: ErrorRule


@dataclasses.dataclass(frozen=True, slots=True)
class ConceptCheck:
    """Comparison of the requested concept vector with the one derived from the trace."""

    requested: ConceptVector
    derived: ConceptVector

    @property
    def missing(self) -> frozenset[str]:
        """Requested concepts that the solution did not use."""
        missing = self.requested.concepts - self.derived.concepts

        return missing

    @property
    def extra(self) -> frozenset[str]:
        """Concepts the solution used but the request did not ask for."""
        extra = self.derived.concepts - self.requested.concepts

        return extra

    @property
    def is_accepted(self) -> bool:
        """Whether the derived vector equals the requested one."""
        is_accepted = self.requested == self.derived

        return is_accepted


@dataclasses.dataclass(frozen=True, slots=True)
class ParameterProblem:
    """A family-specific reason why sampled parameters must not become an item."""

    reason: ParameterReason
    detail: str


@dataclasses.dataclass(frozen=True, slots=True)
class CheckFailure:
    """The first check a variant failed: which stage, a stable reason code, and the numbers."""

    stage: Stage
    reason: Reason
    detail: str


@dataclasses.dataclass(frozen=True, slots=True)
class VerificationReport:
    """The outcome of the verification pipeline for one seed of one family.

    `variant` is set once the question is rendered, `concept_check` once the concept check runs.
    """

    family_name: str
    seed: int
    variant: Variant | None
    concept_check: ConceptCheck | None
    failure: CheckFailure | None

    @property
    def is_accepted(self) -> bool:
        """Whether every stage passed."""
        is_accepted = self.failure is None

        return is_accepted


@dataclasses.dataclass(frozen=True, slots=True)
class TextReading:
    """What a text reader found in a rendered question, and its own answer to it."""

    parameters: collections.abc.Mapping[str, sympy.Basic]
    method: str
    answer: sympy.Basic


class TextReader(typing.Protocol):
    """A family-specific reader of rendered questions, written apart from the family.

    It sees only the text. It must not import the family, or it would repeat a rendering mistake.
    """

    expected_method: str

    def read_question(self, text: str, language: Language) -> TextReading:
        """Parse a question written from the family's controlled template and solve it.

        It raises ValueError when the text does not follow the template.
        """
        ...


class ItemFamily(typing.Protocol):
    """The one API every item family implements, hand-written or generated.

    `render_question` takes the sampled parameters, never the seed, so both languages of a
    variant always show the same numbers.
    """

    name: str
    target_concepts: ConceptVector
    parameter_shapes: collections.abc.Mapping[str, tuple[int, int]]

    def sample_parameters(self, seed: int) -> dict[str, sympy.Basic]:
        """Sample the parameters of one variant from an explicit seed."""
        ...

    def find_parameter_problem(
        self, parameters: collections.abc.Mapping[str, sympy.Basic]
    ) -> ParameterProblem | None:
        """Find an unexpected degenerate case or a non-unique answer, or return None."""
        ...

    def render_question(
        self, parameters: collections.abc.Mapping[str, sympy.Basic], language: Language
    ) -> str:
        """Render the question text in one language."""
        ...

    def solve(self, parameters: collections.abc.Mapping[str, sympy.Basic]) -> sympy.Basic:
        """Compute the answer through step library calls only, so the trace records it."""
        ...

    def compute_reference_answer(
        self, parameters: collections.abc.Mapping[str, sympy.Basic]
    ) -> sympy.Basic:
        """Compute the answer by an independent method, without the step library."""
        ...
