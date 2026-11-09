"""Item families for the linear systems block."""

import collections.abc
import random

import sympy

from la_items import contracts
from la_items.steplib import linear_systems

__all__ = ["Solve2x2LinearSystemGaussian"]

_X, _Y = sympy.symbols("x y")


class Solve2x2LinearSystemGaussian:
    """Solve a 2×2 linear system by Gaussian elimination."""

    name = "solve_2x2_linear_system_gaussian"
    target_concepts = contracts.ConceptVector(
        frozenset({"slae_matrix_form", "elementary_row_ops", "gauss_forward", "back_substitution"})
    )
    parameter_shapes = {"A": (2, 2), "b": (2, 1)}

    def sample_parameters(self, seed: int) -> dict[str, sympy.Basic]:
        """Sample a matrix A until `find_parameter_problem` accepts it, then set b = A·(x, y)."""
        rng = random.Random(seed)
        parameters: dict[str, sympy.Basic] = {
            "A": sympy.ImmutableMatrix.zeros(2, 2),
            "b": sympy.ImmutableMatrix.zeros(2, 1),
        }

        while self.find_parameter_problem(parameters) is not None:
            coefficients = sympy.ImmutableMatrix(2, 2, lambda i, j: rng.randint(-5, 5))
            solution = sympy.ImmutableMatrix(2, 1, lambda i, j: rng.randint(-5, 5))
            parameters = {"A": coefficients, "b": sympy.ImmutableMatrix(coefficients * solution)}

        return parameters

    def find_parameter_problem(
        self, parameters: collections.abc.Mapping[str, sympy.Basic]
    ) -> contracts.ParameterProblem | None:
        """Require det A ≠ 0, so the solution is unique, and a₁₁ ≠ 0, a₂₁ ≠ 0.

        With a₁₁ ≠ 0 and a₂₁ ≠ 0 the solution needs exactly one elimination step, so its trace
        matches the target concepts.
        """
        coefficients = parameters["A"]

        if coefficients.det() == 0:
            problem: contracts.ParameterProblem | None = contracts.ParameterProblem(
                "answer_not_unique", f"det A = 0 for A = {coefficients.tolist()}"
            )

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
        coefficients = parameters["A"]
        constants = parameters["b"]
        equations = "; ".join(
            sympy.sstr(coefficients[i, 0] * _X + coefficients[i, 1] * _Y).replace("*", "")
            + f" = {constants[i, 0]}"
            for i in range(2)
        )
        templates = {
            "uk": "Розв'яжіть систему методом Гаусса: {equations}.",
            "en": "Solve the system by Gaussian elimination: {equations}.",
        }
        question = templates[language].format(equations=equations)

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
        reference_answer = sympy.ImmutableMatrix(parameters["A"].LUsolve(parameters["b"]))

        return reference_answer
