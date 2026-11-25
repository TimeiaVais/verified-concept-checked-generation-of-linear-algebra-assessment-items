import pytest
import sympy

from la_items.steplib import linear_systems, trace


def test_augmented_matrix() -> None:
    with trace.recording() as recorded:
        augmented = linear_systems.augmented_matrix(
            sympy.ImmutableMatrix([[1, 2], [3, 4]]), sympy.ImmutableMatrix([5, 6])
        )

    assert augmented == sympy.ImmutableMatrix([[1, 2, 5], [3, 4, 6]])
    assert recorded == ["slae_matrix_form"]


def test_add_row_multiple() -> None:
    with trace.recording() as recorded:
        transformed = linear_systems.add_row_multiple(
            sympy.ImmutableMatrix([[1, 2], [3, 4]]), 1, 0, sympy.Integer(-3)
        )

    assert transformed == sympy.ImmutableMatrix([[1, 2], [0, -2]])
    assert recorded == ["elementary_row_ops"]


def test_forward_elimination_then_back_substitution() -> None:
    augmented = sympy.ImmutableMatrix([[2, 1, 5], [4, -3, -5]])

    with trace.recording() as recorded:
        echelon = linear_systems.forward_elimination_2x2(augmented)
        solution = linear_systems.back_substitution_2x2(echelon)

    assert echelon == sympy.ImmutableMatrix([[2, 1, 5], [0, -5, -15]])
    assert solution == sympy.ImmutableMatrix([1, 3])
    assert recorded == ["gauss_forward", "elementary_row_ops", "back_substitution"]


def test_fractional_solution_stays_exact() -> None:
    with trace.recording():
        echelon = linear_systems.forward_elimination_2x2(
            sympy.ImmutableMatrix([[3, 1, 1], [1, 2, 0]])
        )
        solution = linear_systems.back_substitution_2x2(echelon)

    assert solution == sympy.ImmutableMatrix([sympy.Rational(2, 5), sympy.Rational(-1, 5)])


def test_zero_pivot_rejected() -> None:
    with trace.recording(), pytest.raises(ValueError, match="pivot is zero"):
        linear_systems.forward_elimination_2x2(sympy.ImmutableMatrix([[0, 1, 1], [1, 2, 0]]))


def test_singular_system_rejected() -> None:
    with trace.recording(), pytest.raises(ValueError, match="no unique solution"):
        linear_systems.back_substitution_2x2(sympy.ImmutableMatrix([[1, 2, 3], [0, 0, 1]]))


def test_cramer_rule() -> None:
    with trace.recording() as recorded:
        solution = linear_systems.cramer_rule_2x2(
            sympy.ImmutableMatrix([[2, 1], [4, -3]]), sympy.ImmutableMatrix([5, -5])
        )

    assert solution == sympy.ImmutableMatrix([1, 3])
    assert recorded == ["cramer_rule", "singularity", "det_2x2", "det_2x2", "det_2x2"]


def test_cramer_rule_keeps_fractions_exact() -> None:
    with trace.recording():
        solution = linear_systems.cramer_rule_2x2(
            sympy.ImmutableMatrix([[3, 1], [1, 2]]), sympy.ImmutableMatrix([1, 0])
        )

    assert solution == sympy.ImmutableMatrix([sympy.Rational(2, 5), sympy.Rational(-1, 5)])


def test_singular_matrix_rejected_by_cramer() -> None:
    with trace.recording(), pytest.raises(ValueError, match="det A = 0"):
        linear_systems.cramer_rule_2x2(
            sympy.ImmutableMatrix([[1, 2], [2, 4]]), sympy.ImmutableMatrix([3, 6])
        )


def test_swap_rows() -> None:
    with trace.recording() as recorded:
        swapped = linear_systems.swap_rows(sympy.ImmutableMatrix([[1, 2], [3, 4]]), 0, 1)

    assert swapped == sympy.ImmutableMatrix([[3, 4], [1, 2]])
    assert recorded == ["elementary_row_ops"]


def test_forward_elimination_swaps_a_zero_pivot() -> None:
    augmented = sympy.ImmutableMatrix([[0, 1, 1, 2], [1, 1, 0, 1], [1, 0, 1, 2]])

    with trace.recording() as recorded:
        echelon = linear_systems.forward_elimination(augmented)
        solution = linear_systems.back_substitution(echelon)

    assert solution == sympy.ImmutableMatrix(augmented[:, :3].LUsolve(augmented[:, 3]))
    assert recorded[:2] == ["gauss_forward", "elementary_row_ops"]
    assert "back_substitution" in recorded


def test_gauss_matches_sympy_on_random_3x3_systems() -> None:
    import random

    rng = random.Random(0)
    solved = 0

    for _ in range(100):
        coefficients = sympy.ImmutableMatrix(3, 3, lambda i, j: rng.randint(-5, 5))
        constants = sympy.ImmutableMatrix(3, 1, lambda i, j: rng.randint(-9, 9))
        if coefficients.det() != 0:
            with trace.recording():
                augmented = linear_systems.augmented_matrix(coefficients, constants)
                solution = linear_systems.back_substitution(
                    linear_systems.forward_elimination(augmented)
                )
            assert solution == sympy.ImmutableMatrix(coefficients.LUsolve(constants))
            solved += 1

    assert solved > 80


def test_forward_elimination_rejects_a_singular_system() -> None:
    with trace.recording(), pytest.raises(ValueError, match="no unique solution"):
        linear_systems.forward_elimination(sympy.ImmutableMatrix([[1, 2, 3], [2, 4, 6]]))


def test_cramer_rule_3x3_uses_cofactor_expansion() -> None:
    with trace.recording() as recorded:
        solution = linear_systems.cramer_rule_3x3(
            sympy.ImmutableMatrix([[2, -1, -1], [3, 4, -2], [3, -2, 4]]),
            sympy.ImmutableMatrix([4, 11, 11]),
        )

    assert solution == sympy.ImmutableMatrix([3, 1, 1])
    assert set(recorded) == {
        "cramer_rule",
        "singularity",
        "cofactor_expansion",
        "minor",
        "cofactor_sign",
        "det_2x2",
    }
