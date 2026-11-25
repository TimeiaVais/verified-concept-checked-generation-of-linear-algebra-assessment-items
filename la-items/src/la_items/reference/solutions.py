"""Solutions of reference exercises, built only from step library calls.

Each solution takes the exercise parameters and returns the answer; the trace of the call gives the
derived concept vector that is compared with the exercise's hand-written label.
"""

import collections.abc
import typing

import sympy

from la_items.steplib import determinants, eigenvalues, linear_systems

__all__ = ["SOLUTIONS"]

Parameters = collections.abc.Mapping[str, sympy.ImmutableMatrix]


def _solve_by_gauss(parameters: Parameters) -> sympy.Basic:
    augmented = linear_systems.augmented_matrix(parameters["A"], parameters["b"])
    solution = linear_systems.back_substitution(linear_systems.forward_elimination(augmented))

    return solution


SOLUTIONS: typing.Final[dict[str, collections.abc.Callable[[Parameters], sympy.Basic]]] = {
    "det_2x2": lambda parameters: determinants.det_2x2(parameters["A"]),
    "det_3x3_triangles": lambda parameters: determinants.det_3x3_rule_of_triangles(parameters["A"]),
    "det_3x3_cofactor": lambda parameters: determinants.cofactor_expansion(parameters["A"]),
    "cramer_2x2": lambda parameters: linear_systems.cramer_rule_2x2(
        parameters["A"], parameters["b"]
    ),
    "cramer_3x3": lambda parameters: linear_systems.cramer_rule_3x3(
        parameters["A"], parameters["b"]
    ),
    "gauss": _solve_by_gauss,
    "eigenvalues_2x2": lambda parameters: eigenvalues.eigenvalues_2x2(parameters["A"]),
    "eigenvalues_3x3": lambda parameters: eigenvalues.eigenvalues_3x3(parameters["A"]),
}
