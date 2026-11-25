"""The necessity test: a step counts only if its output feeds the final answer.

The solution is rerun once per recorded step call, with that call's output spoiled through
`trace.perturbing_call`. If the answer does not change, the answer did not need that call.
"""

import collections.abc
import typing

import sympy

from la_items.steplib import trace

__all__ = ["find_needed_concepts"]

# Offsets 1/p with distinct primes: an integer answer cannot absorb them by coincidence, as it
# can absorb +1 (adding 1 to every entry of (A | b) keeps the solution whenever x + y = 1).
_PRIMES: typing.Final = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53)


def _spoil_step_output(output: typing.Any) -> typing.Any:
    if isinstance(output, sympy.MatrixBase):
        rows, columns = output.shape
        offsets = sympy.ImmutableMatrix(
            rows, columns, lambda i, j: sympy.Rational(1, _PRIMES[(i * columns + j) % 16])
        )
        spoiled = sympy.ImmutableMatrix(output + offsets)

    elif isinstance(output, int | sympy.Expr):
        spoiled = output + sympy.Rational(1, 59)

    else:
        raise TypeError(f"cannot spoil a step output of type {type(output).__name__}")

    return spoiled


def find_needed_concepts(
    solve: collections.abc.Callable[[], sympy.Basic], answer: sympy.Basic, recorded: list[str]
) -> frozenset[str]:
    """Keep a concept only if spoiling at least one of its step calls changes the answer.

    Parameters
    ----------
    solve : Callable[[], sympy.Basic]
        The solution, rerun once per recorded call; it must call the same steps in the same order.
    answer : sympy.Basic
        The answer of the unspoiled run.
    recorded : list[str]
        The trace of the unspoiled run.

    Returns
    -------
    frozenset[str]
        The concepts whose output the answer needs.
    """
    needed: set[str] = set()

    for call_index, concept_id in enumerate(recorded):
        if concept_id not in needed:
            with trace.recording(), trace.perturbing_call(call_index, _spoil_step_output):
                try:
                    is_needed = solve() != answer

                # Any failure caused by the spoiled output shows the answer depended on it.
                except Exception:
                    is_needed = True

            if is_needed:
                needed.add(concept_id)

    needed_concepts = frozenset(needed)

    return needed_concepts
