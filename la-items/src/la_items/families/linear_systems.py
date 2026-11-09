"""Item families for the linear systems block: one 2×2 system, two methods.

The method is named in the question text, because the two methods use different concepts.
"""

import collections.abc
import random

import sympy

from la_items import contracts
from la_items.steplib import linear_systems

__all__ = ["Solve2x2LinearSystemCramer", "Solve2x2LinearSystemGaussian"]

_X, _Y = sympy.symbols("x y")
_ZERO_SYSTEM: dict[str, sympy.Basic] = {
    "A": sympy.ImmutableMatrix.zeros(2, 2),
    "b": sympy.ImmutableMatrix.zeros(2, 1),
}


def _sample_system(
    seed: int,
    find_problem: collections.abc.Callable[
        [collections.abc.Mapping[str, sympy.Basic]], contracts.ParameterProblem | None
    ],
) -> dict[str, sympy.Basic]:
    """Sample A and an integer solution until `find_problem` accepts A, then set b = A·(x, y)."""
    rng = random.Random(seed)
    parameters = _ZERO_SYSTEM

    while find_problem(parameters) is not None:
        coefficients = sympy.ImmutableMatrix(2, 2, lambda i, j: rng.randint(-5, 5))
        solution = sympy.ImmutableMatrix(2, 1, lambda i, j: rng.randint(-5, 5))
        parameters = {"A": coefficients, "b": sympy.ImmutableMatrix(coefficients * solution)}

    return parameters


def _find_singular_matrix(
    parameters: collections.abc.Mapping[str, sympy.Basic],
) -> contracts.ParameterProblem | None:
    coefficients = parameters["A"]
    problem = (
        contracts.ParameterProblem(
            "answer_not_unique", f"det A = 0 for A = {coefficients.tolist()}"
        )
        if coefficients.det() == 0
        else None
    )

    return problem


def _format_equations(parameters: collections.abc.Mapping[str, sympy.Basic]) -> str:
    """Write the system as "-2x + 4y = 16; 3x - 3y = -12"."""
    coefficients = parameters["A"]
    constants = parameters["b"]
    equations = "; ".join(
        sympy.sstr(coefficients[i, 0] * _X + coefficients[i, 1] * _Y).replace("*", "")
        + f" = {constants[i, 0]}"
        for i in range(2)
    )

    return equations


def _solve_with_lu(parameters: collections.abc.Mapping[str, sympy.Basic]) -> sympy.Basic:
    reference_answer = sympy.ImmutableMatrix(parameters["A"].LUsolve(parameters["b"]))

    return reference_answer


class Solve2x2LinearSystemGaussian:
    """Solve a 2×2 linear system by Gaussian elimination."""

    name = "solve_2x2_linear_system_gaussian"
    target_concepts = contracts.ConceptVector(
        frozenset({"slae_matrix_form", "elementary_row_ops", "gauss_forward", "back_substitution"})
    )
    parameter_shapes = {"A": (2, 2), "b": (2, 1)}

    def sample_parameters(self, seed: int) -> dict[str, sympy.Basic]:
        """Sample a system that `find_parameter_problem` accepts."""
        parameters = _sample_system(seed, self.find_parameter_problem)

        return parameters

    def find_parameter_problem(
        self, parameters: collections.abc.Mapping[str, sympy.Basic]
    ) -> contracts.ParameterProblem | None:
        """Require det A ≠ 0, so the solution is unique, and a₁₁ ≠ 0, a₂₁ ≠ 0.

        With a₁₁ ≠ 0 and a₂₁ ≠ 0 the solution needs exactly one elimination step, so its trace
        matches the target concepts.
        """
        coefficients = parameters["A"]
        singular_problem = _find_singular_matrix(parameters)

        if singular_problem is not None:
            problem: contracts.ParameterProblem | None = singular_problem

        elif coefficients[0, 0] == 0 or coefficients[1, 0] == 0:
            problem = contracts.ParameterProblem(
                "degenerate_parameters", f"a11 or a21 is zero in A = {coefficients.tolist()}"
            )

        else:
            problem = None

        return problem

    def render_question(
        self, parameters: collections.abc.Mapping[str, sympy.Basic], language: contracts.Language
    ) -> str:
        """Render the question; it names the method, so the item requires Gaussian elimination."""
        templates = {
            "uk": "Розв'яжіть систему методом Гаусса: {equations}.",
            "en": "Solve the system by Gaussian elimination: {equations}.",
        }
        question = templates[language].format(equations=_format_equations(parameters))

        return question

    def solve(self, parameters: collections.abc.Mapping[str, sympy.Basic]) -> sympy.Basic:
        """Build (A | b), eliminate, and substitute back through the step library."""
        augmented = linear_systems.augmented_matrix(parameters["A"], parameters["b"])
        echelon = linear_systems.forward_elimination_2x2(augmented)
        answer = linear_systems.back_substitution_2x2(echelon)

        return answer

    def compute_reference_answer(
        self, parameters: collections.abc.Mapping[str, sympy.Basic]
    ) -> sympy.Basic:
        """Solve with SymPy's LU decomposition."""
        reference_answer = _solve_with_lu(parameters)

        return reference_answer


class Solve2x2LinearSystemCramer:
    """Solve a 2×2 linear system by Cramer's rule."""

    name = "solve_2x2_linear_system_cramer"
    target_concepts = contracts.ConceptVector(frozenset({"singularity", "det_2x2", "cramer_rule"}))
    parameter_shapes = {"A": (2, 2), "b": (2, 1)}

    def sample_parameters(self, seed: int) -> dict[str, sympy.Basic]:
        """Sample a system that `find_parameter_problem` accepts."""
        parameters = _sample_system(seed, self.find_parameter_problem)

        return parameters

    def find_parameter_problem(
        self, parameters: collections.abc.Mapping[str, sympy.Basic]
    ) -> contracts.ParameterProblem | None:
        """Require det A ≠ 0; Cramer's rule needs nothing else."""
        problem = _find_singular_matrix(parameters)

        return problem

    def render_question(
        self, parameters: collections.abc.Mapping[str, sympy.Basic], language: contracts.Language
    ) -> str:
        """Render the question; it names the method, so the item requires Cramer's rule."""
        templates = {
            "uk": "Розв'яжіть систему за формулами Крамера: {equations}.",
            "en": "Solve the system by Cramer's rule: {equations}.",
        }
        question = templates[language].format(equations=_format_equations(parameters))

        return question

    def solve(self, parameters: collections.abc.Mapping[str, sympy.Basic]) -> sympy.Basic:
        """Apply Cramer's rule through the step library."""
        answer = linear_systems.cramer_rule_2x2(parameters["A"], parameters["b"])

        return answer

    def compute_reference_answer(
        self, parameters: collections.abc.Mapping[str, sympy.Basic]
    ) -> sympy.Basic:
        """Solve with SymPy's LU decomposition."""
        reference_answer = _solve_with_lu(parameters)

        return reference_answer
