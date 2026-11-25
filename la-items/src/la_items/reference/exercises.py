"""Load the reference set: course exercises with hand-written concept labels (ADR-0006)."""

import dataclasses
import pathlib
import typing

import sympy
import yaml

from la_items import contracts
from la_items.reference import solutions

__all__ = ["EXERCISES_PATH", "Exercise", "load_exercises"]

EXERCISES_PATH: typing.Final = pathlib.Path(__file__).with_name("exercises.yaml")


@dataclasses.dataclass(frozen=True, slots=True)
class Exercise:
    """One part of one course exercise, with the concepts its section and method require."""

    id: str
    page: int
    number: str
    section: str
    task: str
    solution: str
    parameters: dict[str, sympy.ImmutableMatrix]
    label: contracts.ConceptVector
    main_concept: str
    book_answer: sympy.Basic
    book_erratum: str | None


def _read_book_answer(text: str) -> sympy.Basic:
    # The answers are written by hand in exercises.yaml, so sympify only ever sees trusted text.
    value = sympy.sympify(text)
    book_answer = sympy.ImmutableMatrix(value) if isinstance(value, list) else value

    return book_answer


def _read_parameters(raw: dict[str, list[typing.Any]]) -> dict[str, sympy.ImmutableMatrix]:
    parameters = {
        name: sympy.ImmutableMatrix([[entry] for entry in rows] if name == "b" else rows)
        for name, rows in raw.items()
    }

    return parameters


def load_exercises(path: pathlib.Path = EXERCISES_PATH) -> list[Exercise]:
    """Read and check the reference set.

    Parameters
    ----------
    path : pathlib.Path
        The YAML file with an `exercises` list.

    Returns
    -------
    list[Exercise]
        The exercises in file order.

    Raises
    ------
    ValueError
        It raises on a duplicate id, an unknown solution, a label concept not in the graph, or a
        main concept outside the label.
    """
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    exercises: list[Exercise] = []

    for item in raw["exercises"]:
        exercise = Exercise(
            id=item["id"],
            page=item["page"],
            number=item["number"],
            section=item["section"],
            task=item["task"],
            solution=item["solution"],
            parameters=_read_parameters(item["parameters"]),
            label=contracts.ConceptVector(frozenset(item["label"])),
            main_concept=item["main_concept"],
            book_answer=_read_book_answer(item["book_answer"]),
            book_erratum=item.get("book_erratum"),
        )
        if any(known.id == exercise.id for known in exercises):
            raise ValueError(f"duplicate exercise id: {exercise.id}")
        if exercise.solution not in solutions.SOLUTIONS:
            raise ValueError(f"{exercise.id}: unknown solution {exercise.solution!r}")
        if exercise.main_concept not in exercise.label.concepts:
            raise ValueError(f"{exercise.id}: main concept {exercise.main_concept!r} not in label")
        exercises.append(exercise)

    return exercises
