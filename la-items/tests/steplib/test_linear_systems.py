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
