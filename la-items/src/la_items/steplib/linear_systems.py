"""Library steps for the linear systems block: Gaussian elimination of a 2×2 system.

Composed, they solve a system with a nonzero first pivot and a nonzero entry under it. The trace
then holds `slae_matrix_form`, `gauss_forward`, `elementary_row_ops` and `back_substitution`.
"""

import sympy

from la_items.steplib import trace

__all__ = [
    "add_row_multiple",
    "augmented_matrix",
    "back_substitution_2x2",
    "forward_elimination_2x2",
]


@trace.step("slae_matrix_form")
def augmented_matrix(
    coefficients: sympy.ImmutableMatrix, constants: sympy.ImmutableMatrix
) -> sympy.ImmutableMatrix:
    """Join the coefficient matrix and the column of constants.

    Parameters
    ----------
    coefficients : sympy.ImmutableMatrix
        The n×n coefficient matrix A.
    constants : sympy.ImmutableMatrix
        The n×1 column b.

    Returns
    -------
    sympy.ImmutableMatrix
        The n×(n+1) augmented matrix (A | b).

    Raises
    ------
    ValueError
        It raises when the shapes do not match.
    """
    if coefficients.rows != constants.rows or constants.cols != 1:
        raise ValueError(f"cannot join {coefficients.shape} and {constants.shape}")
    augmented = sympy.ImmutableMatrix(coefficients.row_join(constants))

    return augmented


@trace.step("elementary_row_ops")
def add_row_multiple(
    matrix: sympy.ImmutableMatrix, target_row: int, source_row: int, factor: sympy.Expr
) -> sympy.ImmutableMatrix:
    """Add `factor` times one row to another row.

    Parameters
    ----------
    matrix : sympy.ImmutableMatrix
        The matrix to transform.
    target_row, source_row : int
        The zero-based rows; the target row changes.
    factor : sympy.Expr
        The multiplier of the source row.

    Returns
    -------
    sympy.ImmutableMatrix
        A new matrix with the target row replaced.

    Raises
    ------
    ValueError
        It raises when both rows are the same.
    """
    if target_row == source_row:
        raise ValueError("target and source rows must differ")
    rows = matrix.tolist()
    rows[target_row] = [
        target + factor * source
        for target, source in zip(rows[target_row], rows[source_row], strict=True)
    ]
    transformed = sympy.ImmutableMatrix(rows)

    return transformed


@trace.step("gauss_forward")
def forward_elimination_2x2(augmented: sympy.ImmutableMatrix) -> sympy.ImmutableMatrix:
    """Eliminate the first unknown from the second equation.

    Parameters
    ----------
    augmented : sympy.ImmutableMatrix
        A 2×3 augmented matrix with a nonzero first pivot.

    Returns
    -------
    sympy.ImmutableMatrix
        The echelon form, with a zero under the first pivot.

    Raises
    ------
    ValueError
        It raises when the matrix is not 2×3 or the first pivot is zero.
    """
    if augmented.shape != (2, 3):
        raise ValueError(f"expected a 2×3 augmented matrix, got {augmented.shape}")
    if augmented[0, 0] == 0:
        raise ValueError("first pivot is zero; a row swap is not a step of this library yet")
    factor = -augmented[1, 0] / augmented[0, 0]
    echelon = add_row_multiple(augmented, 1, 0, factor)

    return echelon


@trace.step("back_substitution")
def back_substitution_2x2(echelon: sympy.ImmutableMatrix) -> sympy.ImmutableMatrix:
    """Find y from the second equation, then x from the first.

    Parameters
    ----------
    echelon : sympy.ImmutableMatrix
        A 2×3 augmented matrix in echelon form.

    Returns
    -------
    sympy.ImmutableMatrix
        The 2×1 solution column (x, y).

    Raises
    ------
    ValueError
        It raises when the matrix is not in echelon form or the system has no unique solution.
    """
    if echelon.shape != (2, 3) or echelon[1, 0] != 0:
        raise ValueError("expected a 2×3 augmented matrix in echelon form")
    if echelon[0, 0] == 0 or echelon[1, 1] == 0:
        raise ValueError("the system has no unique solution")
    y = echelon[1, 2] / echelon[1, 1]
    x = (echelon[0, 2] - echelon[0, 1] * y) / echelon[0, 0]
    solution = sympy.ImmutableMatrix([x, y])

    return solution
