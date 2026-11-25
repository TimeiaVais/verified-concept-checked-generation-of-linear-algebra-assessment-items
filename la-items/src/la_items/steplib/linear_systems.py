"""Library steps for the linear systems block: Gaussian elimination and Cramer's rule.

Gaussian elimination solves a system with a unique solution; its trace holds `slae_matrix_form`,
`gauss_forward`, `elementary_row_ops` and `back_substitution`. The 2×2 steps need a nonzero first
pivot and a nonzero entry under it; the n×n steps swap rows when a pivot is zero.
Cramer's rule solves a 2×2 or 3×3 system with det A ≠ 0; its trace holds `cramer_rule`,
`singularity` and the determinant steps: `det_2x2` for 2×2, and `cofactor_expansion`, `minor`,
`cofactor_sign`, `det_2x2` for 3×3.
"""

import sympy

from la_items.steplib import determinants, trace

__all__ = [
    "add_row_multiple",
    "augmented_matrix",
    "back_substitution",
    "back_substitution_2x2",
    "check_nonsingular",
    "cramer_rule_2x2",
    "cramer_rule_3x3",
    "forward_elimination",
    "forward_elimination_2x2",
    "swap_rows",
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


def _compute_determinant(matrix: sympy.ImmutableMatrix) -> sympy.Expr:
    if matrix.shape == (2, 2):
        determinant = determinants.det_2x2(matrix)

    elif matrix.shape == (3, 3):
        determinant = determinants.cofactor_expansion(matrix)

    else:
        raise ValueError(f"expected a 2×2 or 3×3 matrix, got {matrix.shape}")

    return determinant


@trace.step("singularity")
def check_nonsingular(coefficients: sympy.ImmutableMatrix) -> sympy.Expr:
    """Compute det A of a 2×2 or 3×3 matrix and require det A ≠ 0.

    Parameters
    ----------
    coefficients : sympy.ImmutableMatrix
        A 2×2 or 3×3 coefficient matrix.

    Returns
    -------
    sympy.Expr
        det A, which is not zero.

    Raises
    ------
    ValueError
        It raises when det A = 0 or the matrix has another shape.
    """
    determinant = _compute_determinant(coefficients)
    if determinant == 0:
        raise ValueError("the system has no unique solution: det A = 0")

    return determinant


def _solve_by_cramer(
    coefficients: sympy.ImmutableMatrix, constants: sympy.ImmutableMatrix, size: int
) -> sympy.ImmutableMatrix:
    if coefficients.shape != (size, size) or constants.shape != (size, 1):
        raise ValueError(
            f"expected {size}×{size} and {size}×1, got {coefficients.shape} and {constants.shape}"
        )
    determinant = check_nonsingular(coefficients)
    replaced = [
        sympy.ImmutableMatrix(coefficients.col_del(column).col_insert(column, constants))
        for column in range(size)
    ]
    solution = sympy.ImmutableMatrix(
        [_compute_determinant(matrix) / determinant for matrix in replaced]
    )

    return solution


@trace.step("cramer_rule")
def cramer_rule_2x2(
    coefficients: sympy.ImmutableMatrix, constants: sympy.ImmutableMatrix
) -> sympy.ImmutableMatrix:
    """Solve a 2×2 system as x_j = det A_j / det A, where A_j has column j replaced by b.

    Parameters
    ----------
    coefficients : sympy.ImmutableMatrix
        The 2×2 coefficient matrix A.
    constants : sympy.ImmutableMatrix
        The 2×1 column b.

    Returns
    -------
    sympy.ImmutableMatrix
        The 2×1 solution column (x, y).

    Raises
    ------
    ValueError
        It raises when the shapes are wrong or det A = 0.
    """
    solution = _solve_by_cramer(coefficients, constants, 2)

    return solution


@trace.step("cramer_rule")
def cramer_rule_3x3(
    coefficients: sympy.ImmutableMatrix, constants: sympy.ImmutableMatrix
) -> sympy.ImmutableMatrix:
    """Solve a 3×3 system as x_j = det A_j / det A; the determinants use cofactor expansion.

    Parameters
    ----------
    coefficients : sympy.ImmutableMatrix
        The 3×3 coefficient matrix A.
    constants : sympy.ImmutableMatrix
        The 3×1 column b.

    Returns
    -------
    sympy.ImmutableMatrix
        The 3×1 solution column.

    Raises
    ------
    ValueError
        It raises when the shapes are wrong or det A = 0.
    """
    solution = _solve_by_cramer(coefficients, constants, 3)

    return solution


@trace.step("elementary_row_ops")
def swap_rows(
    matrix: sympy.ImmutableMatrix, first_row: int, second_row: int
) -> sympy.ImmutableMatrix:
    """Swap two rows of a matrix.

    Parameters
    ----------
    matrix : sympy.ImmutableMatrix
        The matrix to transform.
    first_row, second_row : int
        The zero-based rows to swap.

    Returns
    -------
    sympy.ImmutableMatrix
        A new matrix with the two rows swapped.
    """
    rows = matrix.tolist()
    rows[first_row], rows[second_row] = rows[second_row], rows[first_row]
    swapped = sympy.ImmutableMatrix(rows)

    return swapped


@trace.step("gauss_forward")
def forward_elimination(augmented: sympy.ImmutableMatrix) -> sympy.ImmutableMatrix:
    """Bring an n×(n+1) augmented matrix to echelon form with row swaps and row additions.

    Parameters
    ----------
    augmented : sympy.ImmutableMatrix
        The augmented matrix (A | b) of a square system.

    Returns
    -------
    sympy.ImmutableMatrix
        The echelon form, with zeros under every pivot.

    Raises
    ------
    ValueError
        It raises when the shape is wrong or a column has no nonzero pivot, so the solution is
        not unique.
    """
    size = augmented.rows
    if augmented.cols != size + 1:
        raise ValueError(f"expected an n×(n+1) augmented matrix, got {augmented.shape}")
    echelon = augmented

    for column in range(size):
        pivot_rows = [row for row in range(column, size) if echelon[row, column] != 0]
        if not pivot_rows:
            raise ValueError(f"no nonzero pivot in column {column + 1}: no unique solution")

        if pivot_rows[0] != column:
            echelon = swap_rows(echelon, column, pivot_rows[0])

        for row in range(column + 1, size):
            if echelon[row, column] != 0:
                factor = -echelon[row, column] / echelon[column, column]
                echelon = add_row_multiple(echelon, row, column, factor)

    return echelon


@trace.step("back_substitution")
def back_substitution(echelon: sympy.ImmutableMatrix) -> sympy.ImmutableMatrix:
    """Solve an echelon system from the last equation up.

    Parameters
    ----------
    echelon : sympy.ImmutableMatrix
        An n×(n+1) augmented matrix in echelon form with nonzero pivots.

    Returns
    -------
    sympy.ImmutableMatrix
        The n×1 solution column.

    Raises
    ------
    ValueError
        It raises when the matrix is not in echelon form or a pivot is zero.
    """
    size = echelon.rows
    is_echelon = echelon.cols == size + 1 and all(
        echelon[row, column] == 0 for row in range(size) for column in range(row)
    )
    if not is_echelon or any(echelon[row, row] == 0 for row in range(size)):
        raise ValueError("expected an echelon augmented matrix with nonzero pivots")
    unknowns: list[sympy.Expr] = [sympy.Integer(0)] * size

    for row in reversed(range(size)):
        known = sum(echelon[row, column] * unknowns[column] for column in range(row + 1, size))
        unknowns[row] = (echelon[row, size] - known) / echelon[row, row]

    solution = sympy.ImmutableMatrix(unknowns)

    return solution
