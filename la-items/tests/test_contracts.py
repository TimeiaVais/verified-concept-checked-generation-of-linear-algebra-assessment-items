import pytest
import sympy as sp

from contracts import ConceptCheck, ConceptVector, Distractor, ErrorRule, Variant
from steplib.trace import recording, step


@step("det_2x2")
def det2(a: int, b: int, c: int, d: int) -> int:
    return a * d - b * c


@pytest.mark.parametrize("tag", ["Cofactor sign", "det2", "eigenvalues_2x2", "Det_2x2"])
def test_free_text_tag_rejected_in_vector(tag: str) -> None:
    with pytest.raises(ValueError, match="unknown concept"):
        ConceptVector(frozenset({"minor", tag}))


def test_free_text_tag_rejected_in_error_rule() -> None:
    with pytest.raises(ValueError, match="unknown concept"):
        ErrorRule(name="no_sign", broken_concept="cofactor signs")


def test_vector_from_trace_drops_repeats() -> None:
    with recording() as trace:
        det2(1, 2, 3, 4)
        det2(5, 6, 7, 8)
    assert ConceptVector.from_trace(trace) == ConceptVector(frozenset({"det_2x2"}))


def test_concept_check_accepts_equal_vectors() -> None:
    vector = ConceptVector(frozenset({"det_2x2", "minor"}))
    check = ConceptCheck(requested=vector, derived=vector)
    assert check.is_accepted
    assert check.missing == check.extra == frozenset()


def test_concept_check_reports_missing_and_extra() -> None:
    check = ConceptCheck(
        requested=ConceptVector(frozenset({"cofactor_expansion", "cofactor_sign", "det_2x2"})),
        derived=ConceptVector(frozenset({"det_3x3_triangle", "det_2x2"})),
    )
    assert not check.is_accepted
    assert check.missing == {"cofactor_expansion", "cofactor_sign"}
    assert check.extra == {"det_3x3_triangle"}


def test_variant_rejects_mutable_matrix() -> None:
    with pytest.raises(TypeError, match="parameter 'A'"):
        Variant(seed=1, parameters={"A": sp.Matrix([[1]])}, question_text="", answer=sp.Integer(1))


def test_variant_and_distractor_accept_sympy_objects() -> None:
    A = sp.ImmutableMatrix([[1, 2], [3, 4]])
    variant = Variant(seed=1, parameters={"A": A}, question_text="det A?", answer=A.det())
    distractor = Distractor(answer=sp.Integer(10), error_rule=ErrorRule("det2_plus", "det_2x2"))
    assert variant.answer == -2
    assert distractor.error_rule.broken_concept == "det_2x2"
