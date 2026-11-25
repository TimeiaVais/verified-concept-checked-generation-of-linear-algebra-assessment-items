import pathlib

import pytest
import sympy

from la_items.reference import agreement, exercises

EXERCISES = exercises.load_exercises()
RESULTS = {result.exercise_id: result for result in agreement.evaluate_reference_set(EXERCISES)}
ERRATA = {"storozhenko-1.91b", "storozhenko-2.19"}
# In these two matrices the minors of the second and third column of A − λE's first row are zero,
# so the cofactor signs cannot change the eigenvalues; the label, written from the book's method,
# still lists cofactor_sign.
SIGNS_CANNOT_MATTER = {"storozhenko-2.45", "storozhenko-2.47"}


def compute_with_sympy(exercise: exercises.Exercise) -> sympy.Basic:
    matrix = exercise.parameters["A"]

    if exercise.solution.startswith("det"):
        answer = matrix.det()

    elif exercise.solution in {"cramer_2x2", "cramer_3x3", "gauss"}:
        answer = sympy.ImmutableMatrix(matrix.LUsolve(exercise.parameters["b"]))

    else:
        values = [v for v, count in matrix.eigenvals().items() for _ in range(count)]
        answer = sympy.ImmutableMatrix(sorted(values, key=float))

    return answer


def test_reference_set_size_and_ids() -> None:
    assert len(EXERCISES) == 29
    assert len({exercise.id for exercise in EXERCISES}) == 29


@pytest.mark.parametrize("exercise", EXERCISES, ids=lambda exercise: exercise.id)
def test_step_library_answer_matches_sympy(exercise: exercises.Exercise) -> None:
    difference = sympy.simplify(RESULTS[exercise.id].answer - compute_with_sympy(exercise))

    assert difference == 0 or difference.is_zero_matrix


def test_answers_match_the_book_except_documented_errata() -> None:
    mismatched = {exercise_id for exercise_id, result in RESULTS.items() if not result.matches_book}
    documented = {exercise.id for exercise in EXERCISES if exercise.book_erratum}

    assert mismatched == ERRATA == documented


def test_main_concept_is_found_in_every_exercise() -> None:
    assert all(result.has_main_concept for result in RESULTS.values())


def test_exact_agreement_except_where_signs_cannot_matter() -> None:
    disagreeing = {
        exercise_id for exercise_id, result in RESULTS.items() if not result.is_exact_match
    }

    assert disagreeing == SIGNS_CANNOT_MATTER
    for exercise_id in disagreeing:
        assert RESULTS[exercise_id].concept_check.missing == {"cofactor_sign"}
        assert not RESULTS[exercise_id].concept_check.extra


def write_exercise_file(tmp_path: pathlib.Path, **overrides: object) -> pathlib.Path:
    entry = {
        "id": "x-1",
        "page": 1,
        "number": "1",
        "section": "s",
        "task": "t",
        "solution": "det_2x2",
        "parameters": "{A: [[1, 2], [3, 4]]}",
        "label": "[det_2x2]",
        "main_concept": "det_2x2",
        "book_answer": '"-2"',
    }
    entry.update({key: str(value) for key, value in overrides.items()})
    lines = ["  - " + "\n    ".join(f"{key}: {value}" for key, value in entry.items())]
    path = tmp_path / "exercises.yaml"
    path.write_text(
        "exercises:\n"
        + "\n".join(lines * (2 if "duplicate" in overrides else 1)).replace(
            "duplicate: True\n    ", ""
        ),
        encoding="utf-8",
    )

    return path


def test_valid_file_loads(tmp_path: pathlib.Path) -> None:
    (exercise,) = exercises.load_exercises(write_exercise_file(tmp_path))

    assert exercise.book_answer == -2


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"solution": "det_4x4"}, "unknown solution"),
        ({"main_concept": "minor"}, "not in label"),
        ({"label": "[determinant]"}, "unknown concept"),
        ({"duplicate": True}, "duplicate exercise id"),
    ],
)
def test_invalid_file_is_rejected(
    tmp_path: pathlib.Path, overrides: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        exercises.load_exercises(write_exercise_file(tmp_path, **overrides))
