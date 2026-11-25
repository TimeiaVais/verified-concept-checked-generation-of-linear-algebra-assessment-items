import inspect

import pytest

from la_items.families import determinants, eigenvalues, linear_systems
from la_items.generation import static_check

DETERMINANT_SOURCE = inspect.getsource(determinants)
SOLVE_LINE = '        answer = determinants.cofactor_expansion(parameters["A"])'


@pytest.mark.parametrize("module", [determinants, linear_systems, eigenvalues])
def test_hand_written_families_pass(module: object) -> None:
    assert static_check.find_static_failure(inspect.getsource(module)) is None  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        (lambda s: "import os\n" + s, "forbidden_import"),
        (lambda s: "import socket\n" + s, "forbidden_import"),
        (lambda s: "from . import helpers\n" + s, "forbidden_import"),
        (lambda s: "from la_items.steplib import trace\n" + s, "forbidden_import"),
        (lambda s: s + "\nDATA = open('/etc/passwd').read()\n", "forbidden_call"),
        (lambda s: s + "\nCODE = eval('1 + 1')\n", "forbidden_call"),
        (lambda s: s + "\nBASE = int.__subclasses__()\n", "forbidden_call"),
        (lambda s: s.replace("def solve(", "def solve_it("), "missing_family"),
        (
            lambda s: s.replace(SOLVE_LINE, '        answer = parameters["A"].det()'),
            "math_outside_step_library",
        ),
        (lambda s: s.replace(SOLVE_LINE, SOLVE_LINE + " * 1"), "math_outside_step_library"),
        (
            lambda s: s.replace(SOLVE_LINE, "        answer = sympy.Integer(7)"),
            "math_outside_step_library",
        ),
        (lambda s: s + "\ndef broken(:\n", "syntax_error"),
    ],
    ids=[
        "os",
        "socket",
        "relative",
        "trace",
        "open",
        "eval",
        "dunder",
        "no-solve",
        "sympy-det",
        "arithmetic",
        "sympy-call",
        "syntax",
    ],
)
def test_rule_breaks_are_rejected(change: object, reason: str) -> None:
    source = change(DETERMINANT_SOURCE)  # type: ignore[operator]
    assert source != DETERMINANT_SOURCE

    failure = static_check.find_static_failure(source)

    assert failure is not None
    assert (failure.stage, failure.reason) == ("static_check", reason), failure.detail


def test_step_function_imported_by_name_is_allowed() -> None:
    source = DETERMINANT_SOURCE.replace(
        "from la_items.steplib import determinants",
        "from la_items.steplib import determinants\n"
        "from la_items.steplib.determinants import cofactor_expansion",
    ).replace(SOLVE_LINE, '        answer = cofactor_expansion(parameters["A"])')

    assert static_check.find_static_failure(source) is None
