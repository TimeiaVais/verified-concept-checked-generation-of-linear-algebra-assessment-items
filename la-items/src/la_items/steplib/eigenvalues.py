"""Library steps for the eigenvalues block: eigenvalues of a 2×2 matrix.

Composed, they find the eigenvalues as the roots of det(A − λE). The trace then holds `eigenvalue`,
`characteristic_polynomial`, `matrix_linear_ops` and `det_2x2`.
"""

import typing

import sympy

from la_items.steplib import determinants, trace

__all__ = ["LAMBDA", "characteristic_polynomial_2x2", "eigenvalues_2x2", "subtract_lambda_identity"]

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
