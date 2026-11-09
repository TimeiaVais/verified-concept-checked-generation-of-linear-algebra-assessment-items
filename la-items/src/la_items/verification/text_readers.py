"""Stage 3, text-program agreement: readers that see only the rendered question.

Each reader parses one family's controlled template with a regular expression, never `eval`, and
solves the question with SymPy by a method of its own. It does not import the family, so a
rendering mistake there cannot repeat here.
"""

import ast
import re
import typing

import sympy

from la_items import contracts

__all__ = ["DeterminantCofactorTextReader", "EigenvaluesTextReader", "LinearSystemTextReader"]

_ORDINALS: typing.Final = {
    "uk": {"першим": 1, "другим": 2, "третім": 3},
    "en": {"first": 1, "second": 2, "third": 3},
}


def _match_template(pattern: str, text: str) -> re.Match[str]:
    match = re.fullmatch(pattern, text)
    if match is None:
        raise ValueError(f"text does not follow the template: {text!r}")

    return match


def _read_integer_matrix(matrix_text: str) -> sympy.ImmutableMatrix:
    """Read "[[1, -2], [3, 4]]" with `ast.literal_eval`, which evaluates literals only."""
    rows = ast.literal_eval(matrix_text)
    if not all(isinstance(entry, int) for row in rows for entry in row):
        raise ValueError(f"matrix entries are not integers: {matrix_text!r}")
    matrix = sympy.ImmutableMatrix(rows)

    return matrix


class DeterminantCofactorTextReader:
    """Read "compute det A by cofactor expansion along the n-th row, A = [[...], ...]"."""

    expected_method = "cofactor_row_1"
    _templates: typing.Final = {
        "uk": r"Обчисліть визначник матриці A розкладом за (\w+) рядком, A = (\[.*\])\.",
        "en": r"Compute det A by cofactor expansion along the (\w+) row, A = (\[.*\])\.",
    }

    def read_question(self, text: str, language: contracts.Language) -> contracts.TextReading:
        """Parse the expansion row and the matrix, then compute det A by Berkowitz's method."""
        match = _match_template(self._templates[language], text)
        row_word, matrix_text = match.groups()
        if row_word not in _ORDINALS[language]:
            raise ValueError(f"unknown row ordinal {row_word!r}")
        matrix = _read_integer_matrix(matrix_text)
        reading = contracts.TextReading(
            parameters={"A": matrix},
            method=f"cofactor_row_{_ORDINALS[language][row_word]}",
            answer=matrix.det(method="berkowitz"),
        )

        return reading


class LinearSystemTextReader:
    """Read "solve the system by <method>: ax + by = c; dx + ey = f" for either method.

    One reader knows both method templates, so a family whose text names the other method fails
    with a method mismatch, not with unreadable text.
    """

    _templates: typing.Final = {
        "gaussian_elimination": {
            "uk": r"Розв'яжіть систему методом Гаусса: (.*)\.",
            "en": r"Solve the system by Gaussian elimination: (.*)\.",
        },
        "cramer_rule": {
            "uk": r"Розв'яжіть систему за формулами Крамера: (.*)\.",
            "en": r"Solve the system by Cramer's rule: (.*)\.",
        },
    }

    def __init__(self, expected_method: str) -> None:
        if expected_method not in self._templates:
            raise ValueError(f"unknown method {expected_method!r}")
        self.expected_method = expected_method

    def read_question(self, text: str, language: contracts.Language) -> contracts.TextReading:
        """Find which method template the text follows, parse the equations, solve with linsolve."""
        matches = {
            method: re.fullmatch(templates[language], text)
            for method, templates in self._templates.items()
        }
        found = [(method, match) for method, match in matches.items() if match is not None]
        if not found:
            raise ValueError(f"text does not follow a system template: {text!r}")
        method, match = found[0]
        equations = [self._read_equation(equation) for equation in match.group(1).split("; ")]
        if len(equations) != 2:
            raise ValueError(f"expected 2 equations, got {len(equations)}")
        coefficients = sympy.ImmutableMatrix([row for row, _ in equations])
        constants = sympy.ImmutableMatrix([constant for _, constant in equations])
        x, y = sympy.symbols("x y")
        (solution,) = sympy.linsolve((coefficients, constants), x, y)
        reading = contracts.TextReading(
            parameters={"A": coefficients, "b": constants},
            method=method,
            answer=sympy.ImmutableMatrix(solution),
        )

        return reading

    @staticmethod
    def _read_equation(equation: str) -> tuple[list[int], int]:
        """Read "-2x + 4y = 16" as ([-2, 4], 16); a missing term has coefficient 0."""
        match = _match_template(r"(.+) = (-?\d+)", equation)
        left_side = match.group(1).replace(" ", "")
        if not re.fullmatch(r"(?:[+-]?\d*[xy])+", left_side):
            raise ValueError(f"left side is not a sum of x and y terms: {equation!r}")
        terms = re.findall(r"([+-]?)(\d*)([xy])", left_side)
        variables = [variable for _, _, variable in terms]
        if len(set(variables)) != len(variables):
            raise ValueError(f"a variable appears twice: {equation!r}")
        coefficient_by_variable = {
            variable: (-1 if sign == "-" else 1) * int(digits or 1)
            for sign, digits, variable in terms
        }
        row_and_constant = (
            [coefficient_by_variable.get("x", 0), coefficient_by_variable.get("y", 0)],
            int(match.group(2)),
        )

        return row_and_constant


class EigenvaluesTextReader:
    """Read "find the eigenvalues of A using the characteristic polynomial, A = [[...]]"."""

    expected_method = "characteristic_polynomial"
    _templates: typing.Final = {
        "uk": (
            r"Знайдіть власні значення матриці A за допомогою характеристичного многочлена,"
            r" A = (\[.*\])\. Запишіть їх у порядку зростання\."
        ),
        "en": (
            r"Find the eigenvalues of A using the characteristic polynomial, A = (\[.*\])\."
            r" List them in increasing order\."
        ),
    }

    def read_question(self, text: str, language: contracts.Language) -> contracts.TextReading:
        """Parse the matrix, then solve det(A − λE) = 0 with `sympy.solve`, in increasing order."""
        match = _match_template(self._templates[language], text)
        matrix = _read_integer_matrix(match.group(1))
        lam = sympy.Symbol("lambda")
        roots = sympy.solve((matrix - lam * sympy.eye(2)).det(), lam)
        reading = contracts.TextReading(
            parameters={"A": matrix},
            method="characteristic_polynomial",
            answer=sympy.ImmutableMatrix(sorted(roots)),
        )

        return reading
