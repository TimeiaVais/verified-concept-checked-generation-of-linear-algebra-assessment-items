"""Library steps for the eigenvalues block: eigenvalues of a 2×2 or 3×3 matrix.

Composed, they find the eigenvalues as the roots of det(A − λE). For 2×2 the trace holds
`eigenvalue`, `characteristic_polynomial`, `matrix_linear_ops` and `det_2x2`; for 3×3 the
determinant is a cofactor expansion, which adds `cofactor_expansion`, `minor` and `cofactor_sign`.
"""

import typing

import sympy

from la_items.steplib import determinants, trace

__all__ = [
    "LAMBDA",
    "characteristic_polynomial_2x2",
    "characteristic_polynomial_3x3",
    "eigenvalues_2x2",
    "eigenvalues_3x3",
    "subtract_lambda_identity",
]

LAMBDA: typing.Final = sympy.Symbol("lambda")


@trace.step("matrix_linear_ops")
def subtract_lambda_identity(matrix: sympy.ImmutableMatrix) -> sympy.ImmutableMatrix:
    """Form A − λE.

    Parameters
    ----------
    matrix : sympy.ImmutableMatrix
        A square matrix A.

    Returns
    -------
    sympy.ImmutableMatrix
        A − λE, with λ = `LAMBDA`.

    Raises
    ------
    ValueError
        It raises when the matrix is not square.
    """
    if not matrix.is_square:
        raise ValueError(f"expected a square matrix, got {matrix.shape}")
    shifted = sympy.ImmutableMatrix(matrix - LAMBDA * sympy.eye(matrix.rows))

    return shifted


@trace.step("characteristic_polynomial")
def characteristic_polynomial_2x2(matrix: sympy.ImmutableMatrix) -> sympy.Expr:
    """Compute det(A − λE) of a 2×2 matrix.

    Parameters
    ----------
    matrix : sympy.ImmutableMatrix
        A 2×2 matrix.

    Returns
    -------
    sympy.Expr
        The expanded polynomial in `LAMBDA`.
    """
    polynomial = sympy.expand(determinants.det_2x2(subtract_lambda_identity(matrix)))

    return polynomial


@trace.step("eigenvalue")
def eigenvalues_2x2(matrix: sympy.ImmutableMatrix) -> sympy.ImmutableMatrix:
    """Find the real eigenvalues of a 2×2 matrix with the quadratic formula.

    Parameters
    ----------
    matrix : sympy.ImmutableMatrix
        A 2×2 matrix.

    Returns
    -------
    sympy.ImmutableMatrix
        A 2×1 column of the eigenvalues in increasing order; a repeated eigenvalue appears twice.

    Raises
    ------
    ValueError
        It raises when the eigenvalues are not real.
    """
    _, linear, constant = sympy.Poly(characteristic_polynomial_2x2(matrix), LAMBDA).all_coeffs()
    discriminant = linear**2 - 4 * constant
    if discriminant < 0:
        raise ValueError(f"no real eigenvalues: the discriminant is {discriminant}")
    root = sympy.sqrt(discriminant)
    eigenvalues = sympy.ImmutableMatrix([(-linear - root) / 2, (-linear + root) / 2])

    return eigenvalues


@trace.step("characteristic_polynomial")
def characteristic_polynomial_3x3(matrix: sympy.ImmutableMatrix) -> sympy.Expr:
    """Compute det(A − λE) of a 3×3 matrix by cofactor expansion along the first row.

    Parameters
    ----------
    matrix : sympy.ImmutableMatrix
        A 3×3 matrix.

    Returns
    -------
    sympy.Expr
        The expanded polynomial in `LAMBDA`.
    """
    polynomial = sympy.expand(determinants.cofactor_expansion(subtract_lambda_identity(matrix)))

    return polynomial


def _find_integer_root(coefficients: list[sympy.Expr]) -> sympy.Integer:
    """Return an integer root of a monic cubic λ³ + pλ² + qλ + r with integer coefficients."""
    _, p, q, r = coefficients
    divisors = [d for d in range(1, abs(int(r)) + 1) if r % d == 0] if r != 0 else [0]
    candidates = [sign * d for d in divisors for sign in (1, -1)]
    roots = [c for c in candidates if c**3 + p * c**2 + q * c + r == 0]
    if not roots:
        raise ValueError("the characteristic polynomial has no integer root")
    root = sympy.Integer(roots[0])

    return root


@trace.step("eigenvalue")
def eigenvalues_3x3(matrix: sympy.ImmutableMatrix) -> sympy.ImmutableMatrix:
    """Find the real eigenvalues of a 3×3 matrix when one of them is an integer.

    An integer root is found among the divisors of the constant term; dividing it out leaves a
    quadratic, solved with the quadratic formula.

    Parameters
    ----------
    matrix : sympy.ImmutableMatrix
        A 3×3 matrix with integer entries.

    Returns
    -------
    sympy.ImmutableMatrix
        A 3×1 column of the eigenvalues in increasing order, repeated ones repeated.

    Raises
    ------
    ValueError
        It raises when there is no integer root or an eigenvalue is not real.
    """
    leading, *rest = sympy.Poly(characteristic_polynomial_3x3(matrix), LAMBDA).all_coeffs()
    monic = [sympy.Integer(1)] + [coefficient / leading for coefficient in rest]
    root = _find_integer_root(monic)
    linear = monic[1] + root
    constant = monic[2] + root * linear
    discriminant = linear**2 - 4 * constant
    if discriminant < 0:
        raise ValueError(f"no real eigenvalues: the discriminant is {discriminant}")
    square_root = sympy.sqrt(discriminant)
    found = [root, (-linear - square_root) / 2, (-linear + square_root) / 2]
    eigenvalues = sympy.ImmutableMatrix(sorted(found, key=lambda value: float(value)))

    return eigenvalues
