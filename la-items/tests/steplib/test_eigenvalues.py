import random

import pytest
import sympy

from la_items.steplib import eigenvalues, trace


def test_subtract_lambda_identity() -> None:
    with trace.recording() as recorded:
        shifted = eigenvalues.subtract_lambda_identity(sympy.ImmutableMatrix([[4, 1], [2, 3]]))

    lam = eigenvalues.LAMBDA
    assert shifted == sympy.ImmutableMatrix([[4 - lam, 1], [2, 3 - lam]])
    assert recorded == ["matrix_linear_ops"]


def test_characteristic_polynomial() -> None:
    with trace.recording() as recorded:
        polynomial = eigenvalues.characteristic_polynomial_2x2(
            sympy.ImmutableMatrix([[4, 1], [2, 3]])
        )

    lam = eigenvalues.LAMBDA
    assert sympy.expand(polynomial - (lam**2 - 7 * lam + 10)) == 0
    assert recorded == ["characteristic_polynomial", "matrix_linear_ops", "det_2x2"]


def test_eigenvalues_in_increasing_order() -> None:
    with trace.recording() as recorded:
        found = eigenvalues.eigenvalues_2x2(sympy.ImmutableMatrix([[4, 1], [2, 3]]))

    assert found == sympy.ImmutableMatrix([2, 5])
    assert set(recorded) == {
        "eigenvalue",
        "characteristic_polynomial",
        "matrix_linear_ops",
        "det_2x2",
    }


def test_eigenvalues_match_sympy_eigenvals() -> None:
    rng = random.Random(0)

    for _ in range(200):
        matrix = sympy.ImmutableMatrix(2, 2, lambda i, j: rng.randint(-5, 5))
        if matrix.trace() ** 2 - 4 * matrix.det() >= 0:
            expected = sorted(
                value
                for value, multiplicity in matrix.eigenvals().items()
                for _ in range(multiplicity)
            )
            with trace.recording():
                found = eigenvalues.eigenvalues_2x2(matrix)
            assert [sympy.simplify(a - b) for a, b in zip(found, expected, strict=True)] == [0, 0]


def test_complex_eigenvalues_rejected() -> None:
    with trace.recording(), pytest.raises(ValueError, match="no real eigenvalues"):
        eigenvalues.eigenvalues_2x2(sympy.ImmutableMatrix([[0, -1], [1, 0]]))
