"""Library steps for the determinants block.

Each step records its graph concept when called. Composed, they give the full
solution "3×3 determinant by cofactor expansion along the first row", whose
trace holds `cofactor_expansion`, `minor`, `cofactor_sign` and `det_2x2`.
"""

import sympy

from la_items.steplib import trace

__all__ = ["cofactor_expansion", "cofactor_sign", "det_2x2", "minor"]


def _check_shape(matrix: sympy.ImmutableMatrix, size: int) -> None:
    if matrix.shape != (size, size):
        raise ValueError(f"expected a {size}×{size} matrix, got {matrix.shape}")


@trace.step("det_2x2")
def det_2x2(matrix: sympy.ImmutableMatrix) -> sympy.Expr:
    """Compute a 2×2 determinant as ad − bc.

    Parameters
    ----------
    matrix : sympy.ImmutableMatrix
        A 2×2 matrix.

    Returns
    -------
    sympy.Expr
        The determinant.

    Raises
    ------
    ValueError
        It raises when the matrix is not 2×2.
    """
    _check_shape(matrix, 2)
    determinant = matrix[0, 0] * matrix[1, 1] - matrix[0, 1] * matrix[1, 0]

    return determinant


@trace.step("minor")
def minor(matrix: sympy.ImmutableMatrix, row: int, column: int) -> sympy.Expr:
    """Compute the minor of one entry of a 3×3 matrix.

    Parameters
    ----------
    matrix : sympy.ImmutableMatrix
        A 3×3 matrix.
    row, column : int
        The zero-based position of the entry.

    Returns
    -------
    sympy.Expr
        The determinant of the 2×2 matrix left after deleting the row and the column.

    Raises
    ------
    ValueError
        It raises when the matrix is not 3×3.
    """
    # shortcut: 3×3 only, so the minor is always a 2×2 determinant; generalise for 4×4 items.
    _check_shape(matrix, 3)
    entry_minor = det_2x2(matrix.minor_submatrix(row, column))

    return entry_minor


@trace.step("cofactor_sign")
def cofactor_sign(row: int, column: int) -> int:
    """Return the sign (−1)^(row + column) of a cofactor.

    Parameters
    ----------
    row, column : int
        The zero-based position of the entry. Zero-based and one-based positions give the same
        sign, since both indices shift by one.

    Returns
    -------
    int
        1 or −1.
    """
    sign = 1 if (row + column) % 2 == 0 else -1

    return sign


@trace.step("cofactor_expansion")
def cofactor_expansion(matrix: sympy.ImmutableMatrix) -> sympy.Expr:
    """Compute a 3×3 determinant by cofactor expansion along the first row.

    Parameters
    ----------
    matrix : sympy.ImmutableMatrix
        A 3×3 matrix.

    Returns
    -------
    sympy.Expr
        The determinant.

    Raises
    ------
    ValueError
        It raises when the matrix is not 3×3.
    """
    _check_shape(matrix, 3)
    determinant = sympy.Integer(0)

    for column in range(3):
        determinant += matrix[0, column] * cofactor_sign(0, column) * minor(matrix, 0, column)

    return determinant
