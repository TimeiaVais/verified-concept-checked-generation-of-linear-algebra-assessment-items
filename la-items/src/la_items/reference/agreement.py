"""Compare trace-derived concept vectors with the hand-written labels of the reference set.

Agreement is reported at the two levels the labels support (ADR-0006): the exact vector, and the
main concept of the exercise's section.
"""

import collections.abc
import dataclasses

import sympy

from la_items import contracts
from la_items.reference import exercises as exercise_set
from la_items.reference import solutions
from la_items.steplib import trace
from la_items.verification import necessity

__all__ = ["ExerciseResult", "evaluate_exercise", "evaluate_reference_set"]


@dataclasses.dataclass(frozen=True, slots=True)
class ExerciseResult:
    """The encoded solution of one exercise, checked against the book and against its label."""

    exercise_id: str
    answer: sympy.Basic
    matches_book: bool
    concept_check: contracts.ConceptCheck
    has_main_concept: bool

    @property
    def is_exact_match(self) -> bool:
        """Whether the derived vector equals the label."""
        is_exact_match = self.concept_check.is_accepted

        return is_exact_match


def _is_same_answer(answer: sympy.Basic, book_answer: sympy.Basic) -> bool:
    difference = sympy.simplify(answer - book_answer)
    is_zero = (
        difference.is_zero_matrix if isinstance(difference, sympy.MatrixBase) else difference == 0
    )
    is_same = bool(is_zero)

    return is_same


def evaluate_exercise(exercise: exercise_set.Exercise) -> ExerciseResult:
    """Run the exercise's step-library solution and compare its answer and concepts.

    Parameters
    ----------
    exercise : Exercise
        The exercise.

    Returns
    -------
    ExerciseResult
        The answer, whether it matches the book, and the label comparison.
    """
    solve = solutions.SOLUTIONS[exercise.solution]

    with trace.recording() as recorded:
        answer = solve(exercise.parameters)

    needed = necessity.find_needed_concepts(lambda: solve(exercise.parameters), answer, recorded)
    derived = contracts.ConceptVector(needed)
    result = ExerciseResult(
        exercise_id=exercise.id,
        answer=answer,
        matches_book=_is_same_answer(answer, exercise.book_answer),
        concept_check=contracts.ConceptCheck(requested=exercise.label, derived=derived),
        has_main_concept=exercise.main_concept in derived.concepts,
    )

    return result


def evaluate_reference_set(
    exercises: collections.abc.Iterable[exercise_set.Exercise],
) -> list[ExerciseResult]:
    """Evaluate every exercise, in order.

    Parameters
    ----------
    exercises : Iterable[Exercise]
        The reference set, as `load_exercises` returns it.

    Returns
    -------
    list[ExerciseResult]
        One result per exercise.
    """
    results = [evaluate_exercise(exercise) for exercise in exercises]

    return results
