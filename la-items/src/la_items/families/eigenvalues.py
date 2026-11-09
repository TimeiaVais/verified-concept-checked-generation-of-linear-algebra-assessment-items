"""Item families for the eigenvalues block."""

import collections.abc
import random

import sympy

from la_items import contracts
from la_items.steplib import eigenvalues

__all__ = ["Eigenvalues2x2CharacteristicPolynomial"]


class Eigenvalues2x2CharacteristicPolynomial:
    """Find the eigenvalues of a 2×2 matrix as the roots of its characteristic polynomial."""

    name = "eigenvalues_2x2_characteristic_polynomial"
    target_concepts = contracts.ConceptVector(
        frozenset({"matrix_linear_ops", "det_2x2", "characteristic_polynomial", "eigenvalue"})
    )
    parameter_shapes = {"A": (2, 2)}

    def sample_parameters(self, seed: int) -> dict[str, sympy.Basic]:
        """Sample a 2×2 matrix with entries from −5 to 5 that `find_parameter_problem` accepts."""
        rng = random.Random(seed)
        parameters: dict[str, sympy.Basic] = {"A": sympy.ImmutableMatrix.zeros(2, 2)}

        while self.find_parameter_problem(parameters) is not None:
            parameters = {"A": sympy.ImmutableMatrix(2, 2, lambda i, j: rng.randint(-5, 5))}

        return parameters

    def find_parameter_problem(
        self, parameters: collections.abc.Mapping[str, sympy.Basic]
    ) -> contracts.ParameterProblem | None:
        """Require two distinct integer eigenvalues.

        The discriminant of λ² − (tr A)λ + det A must be a positive perfect square. Complex,
        repeated or irrational eigenvalues would make it another kind of exercise.
        """
        matrix = parameters["A"]
        discriminant = matrix.trace() ** 2 - 4 * matrix.det()
        is_perfect_square = discriminant >= 0 and sympy.sqrt(discriminant).is_integer

        if discriminant <= 0:
            problem: contracts.ParameterProblem | None = contracts.ParameterProblem(
                "degenerate_parameters",
                f"eigenvalues are complex or repeated: discriminant {discriminant}",
            )

        elif not is_perfect_square:
            problem = contracts.ParameterProblem(
                "degenerate_parameters", f"eigenvalues are irrational: discriminant {discriminant}"
            )

        else:
            problem = None

        return problem

    def render_question(
        self, parameters: collections.abc.Mapping[str, sympy.Basic], language: contracts.Language
    ) -> str:
        """Render the question; it names the method and the order of the answer."""
        rows = parameters["A"].tolist()
        templates = {
            "uk": (
                "Знайдіть власні значення матриці A за допомогою характеристичного многочлена,"
                " A = {rows}. Запишіть їх у порядку зростання."
            ),
            "en": (
                "Find the eigenvalues of A using the characteristic polynomial, A = {rows}."
                " List them in increasing order."
            ),
        }
        question = templates[language].format(rows=rows)

        return question

    def solve(self, parameters: collections.abc.Mapping[str, sympy.Basic]) -> sympy.Basic:
        """Find the roots of det(A − λE) through the step library."""
        answer = eigenvalues.eigenvalues_2x2(parameters["A"])

        return answer

    def compute_reference_answer(
        self, parameters: collections.abc.Mapping[str, sympy.Basic]
    ) -> sympy.Basic:
        """Use SymPy's `Matrix.eigenvals()`, sorted."""
        reference_answer = sympy.ImmutableMatrix(sorted(parameters["A"].eigenvals()))

        return reference_answer
