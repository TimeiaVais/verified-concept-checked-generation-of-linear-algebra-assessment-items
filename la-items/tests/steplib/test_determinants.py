import random

import pytest
import sympy

from la_items import contracts
from la_items.steplib import determinants, trace


def test_det_2x2() -> None:
    with trace.recording() as recorded:
        determinant = determinants.det_2x2(sympy.ImmutableMatrix([[1, 2], [3, 4]]))

    assert determinant == -2
    assert recorded == ["det_2x2"]


def test_minor_records_det_2x2() -> None:
    matrix = sympy.ImmutableMatrix([[1, 2, 3], [4, 5, 6], [7, 8, 10]])

    with trace.recording() as recorded:
        entry_minor = determinants.minor(matrix, 0, 1)

    assert entry_minor == 4 * 10 - 6 * 7
    assert recorded == ["minor", "det_2x2"]


@pytest.mark.parametrize(
    ("row", "column", "sign"), [(0, 0, 1), (0, 1, -1), (0, 2, 1), (1, 0, -1), (1, 1, 1)]
)
def test_cofactor_sign(row: int, column: int, sign: int) -> None:
    with trace.recording():
        assert determinants.cofactor_sign(row, column) == sign


def test_cofactor_expansion_matches_sympy_det() -> None:
    rng = random.Random(0)

    for _ in range(200):
        matrix = sympy.ImmutableMatrix(3, 3, lambda i, j: rng.randint(-4, 4))

        with trace.recording():
            assert determinants.cofactor_expansion(matrix) == matrix.det()


def test_cofactor_expansion_trace_gives_the_four_concepts() -> None:
    matrix = sympy.ImmutableMatrix([[2, -1, 0], [1, 3, 4], [0, 5, -2]])

    with trace.recording() as recorded:
        determinants.cofactor_expansion(matrix)

    requested = contracts.ConceptVector(
        frozenset({"cofactor_expansion", "minor", "cofactor_sign", "det_2x2"})
    )
    check = contracts.ConceptCheck(
        requested=requested, derived=contracts.ConceptVector.from_trace(recorded)
    )
    assert check.is_accepted
    assert recorded[:4] == ["cofactor_expansion", "cofactor_sign", "minor", "det_2x2"]


@pytest.mark.parametrize(
    ("step", "matrix"),
    [
        (determinants.det_2x2, sympy.ImmutableMatrix([[1, 2, 3]])),
        (determinants.cofactor_expansion, sympy.ImmutableMatrix([[1, 2], [3, 4]])),
    ],
)
def test_wrong_shape_rejected(step: object, matrix: sympy.ImmutableMatrix) -> None:
    with trace.recording(), pytest.raises(ValueError, match="expected a"):
        step(matrix)  # type: ignore[operator]
