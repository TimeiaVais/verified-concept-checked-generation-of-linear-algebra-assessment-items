"""Stage 1, parameter validity: checks that do not trust the family's sampler."""

import collections.abc
import typing

import sympy

from la_items import contracts

__all__ = [
    "MAX_ANSWER_NUMBER",
    "MAX_ANSWER_OPERATIONS",
    "MAX_PARAMETER_ENTRY",
    "find_answer_failure",
    "find_parameter_failure",
]

MAX_PARAMETER_ENTRY: typing.Final = 100
MAX_ANSWER_NUMBER: typing.Final = 10_000
MAX_ANSWER_OPERATIONS: typing.Final = 30


def _list_entries(value: sympy.Basic) -> list[sympy.Basic]:
    entries = list(value) if isinstance(value, sympy.MatrixBase) else [value]

    return entries


def _fail(reason: contracts.Reason, detail: str) -> contracts.CheckFailure:
    failure = contracts.CheckFailure("parameter_validity", reason, detail)

    return failure


def find_parameter_failure(
    family: contracts.ItemFamily, parameters: collections.abc.Mapping[str, sympy.Basic]
) -> contracts.CheckFailure | None:
    """Check the names, shapes and size of the parameters, then the family's own conditions.

    Parameters
    ----------
    family : contracts.ItemFamily
        The family that sampled the parameters.
    parameters : Mapping[str, sympy.Basic]
        The sampled parameters.

    Returns
    -------
    contracts.CheckFailure | None
        The first problem found, or None.
    """
    shapes = {
        name: value.shape if isinstance(value, sympy.MatrixBase) else None
        for name, value in parameters.items()
    }
    large_entries = [
        entry
        for value in parameters.values()
        for entry in _list_entries(value)
        if not entry.is_number or abs(entry) > MAX_PARAMETER_ENTRY
    ]

    if shapes != dict(family.parameter_shapes):
        failure: contracts.CheckFailure | None = _fail(
            "wrong_shape", f"expected {dict(family.parameter_shapes)}, got {shapes}"
        )

    elif large_entries:
        failure = _fail(
            "number_too_large",
            f"entries {large_entries} are not numbers within ±{MAX_PARAMETER_ENTRY}",
        )

    else:
        problem = family.find_parameter_problem(parameters)
        failure = None if problem is None else _fail(problem.reason, problem.detail)

    return failure


def find_answer_failure(answer: sympy.Basic) -> contracts.CheckFailure | None:
    """Check that the answer is finite, small and short.

    Parameters
    ----------
    answer : sympy.Basic
        The answer of the step-library solution.

    Returns
    -------
    contracts.CheckFailure | None
        The first problem found, or None.
    """
    entries = _list_entries(answer)
    numbers = [number for entry in entries for number in entry.atoms(sympy.Rational)]
    large_numbers = [
        number for number in numbers if max(abs(number.p), number.q) > MAX_ANSWER_NUMBER
    ]
    operations = sum(sympy.count_ops(entry) for entry in entries)

    if any(entry.has(sympy.zoo, sympy.nan, sympy.oo, -sympy.oo) for entry in entries):
        failure = _fail("division_by_zero", f"answer {answer} is not finite")

    elif large_numbers:
        failure = _fail(
            "number_too_large", f"answer numbers {large_numbers} exceed {MAX_ANSWER_NUMBER}"
        )

    elif operations > MAX_ANSWER_OPERATIONS:
        failure = _fail(
            "expression_too_large",
            f"answer has {operations} operations, more than {MAX_ANSWER_OPERATIONS}",
        )

    else:
        failure = None

    return failure
