"""Item families for the determinants block."""

import collections.abc
import random

import sympy

from la_items import contracts
from la_items.steplib import determinants

__all__ = ["Determinant3x3CofactorRow1"]


class Determinant3x3CofactorRow1:
    """Compute a 3×3 determinant by cofactor expansion along the first row."""

    name = "determinant_3x3_cofactor_row_1"
    target_concepts = contracts.ConceptVector(
        frozenset({"cofactor_expansion", "cofactor_sign", "minor", "det_2x2"})
    )

    def sample_parameters(self, seed: int) -> dict[str, sympy.Basic]:
        """Sample a 3×3 matrix with entries from −4 to 4."""
        rng = random.Random(seed)
        parameters: dict[str, sympy.Basic] = {
            "A": sympy.ImmutableMatrix(3, 3, lambda i, j: rng.randint(-4, 4))
        }

        return parameters

    def render_question(
        self, parameters: collections.abc.Mapping[str, sympy.Basic], language: contracts.Language
    ) -> str:
        """Render the question; it names the method, so the item requires cofactor expansion."""
        rows = parameters["A"].tolist()
        templates = {
            "uk": "Обчисліть визначник матриці A розкладом за першим рядком, A = {rows}.",
            "en": "Compute det A by cofactor expansion along the first row, A = {rows}.",
        }
        question = templates[language].format(rows=rows)

        return question

    def solve(self, parameters: collections.abc.Mapping[str, sympy.Basic]) -> sympy.Basic:
        """Expand along the first row through the step library."""
        answer = determinants.cofactor_expansion(parameters["A"])

        return answer

    def compute_reference_answer(
        self, parameters: collections.abc.Mapping[str, sympy.Basic]
    ) -> sympy.Basic:
        """Compute the determinant with SymPy's own `Matrix.det()`."""
        reference_answer = parameters["A"].det()

        return reference_answer
