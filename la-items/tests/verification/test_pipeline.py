import collections.abc

import pytest
import sympy

from la_items import contracts
from la_items.families import determinants, eigenvalues, linear_systems
from la_items.steplib import determinants as determinant_steps
from la_items.verification import parameters, pipeline, text_readers

Parameters = collections.abc.Mapping[str, sympy.Basic]

DETERMINANT = determinants.Determinant3x3CofactorRow1
SYSTEM = linear_systems.Solve2x2LinearSystemGaussian
CRAMER = linear_systems.Solve2x2LinearSystemCramer
EIGENVALUES = eigenvalues.Eigenvalues2x2CharacteristicPolynomial
DETERMINANT_READER = text_readers.DeterminantCofactorTextReader()
SYSTEM_READER = text_readers.LinearSystemTextReader("gaussian_elimination")
CRAMER_READER = text_readers.LinearSystemTextReader("cramer_rule")
EIGENVALUES_READER = text_readers.EigenvaluesTextReader()
ONES = sympy.ImmutableMatrix.ones(3, 3)


# --- Real families -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("family", "reader"),
    [
        (DETERMINANT(), DETERMINANT_READER),
        (SYSTEM(), SYSTEM_READER),
        (CRAMER(), CRAMER_READER),
        (EIGENVALUES(), EIGENVALUES_READER),
    ],
    ids=["determinant", "gauss", "cramer", "eigenvalues"],
)
def test_real_families_pass_every_stage_on_200_seeds(
    family: contracts.ItemFamily, reader: contracts.TextReader
) -> None:
    reports = pipeline.verify_family(family, reader, range(200))

    assert [report.failure for report in reports if not report.is_accepted] == []
    assert all(report.variant is not None for report in reports)
    assert all(report.concept_check and report.concept_check.is_accepted for report in reports)


def test_same_seed_gives_same_report() -> None:
    first = pipeline.verify_variant(SYSTEM(), SYSTEM_READER, 7)
    second = pipeline.verify_variant(SYSTEM(), SYSTEM_READER, 7)

    assert first == second


def test_both_languages_show_the_same_numbers() -> None:
    variant = pipeline.verify_variant(DETERMINANT(), DETERMINANT_READER, 3).variant

    assert variant is not None
    assert variant.question_uk != variant.question_en
    assert variant.question_uk.split("A = ")[-1] == variant.question_en.split("A = ")[-1]


def test_determinant_answer_matches_sympy_det() -> None:
    variant = pipeline.verify_variant(DETERMINANT(), DETERMINANT_READER, 11).variant

    assert variant is not None
    assert variant.answer == variant.parameters["A"].det()


# --- Mutants: each breaks one thing, and the pipeline must name it ------------------------------


def fixed_parameters(**values: list[list[int]]) -> collections.abc.Callable[..., dict]:
    def sample_parameters(self: object, seed: int) -> dict[str, sympy.Basic]:
        return {name: sympy.ImmutableMatrix(rows) for name, rows in values.items()}

    return sample_parameters


class WrongShape(DETERMINANT):
    sample_parameters = fixed_parameters(A=[[1, 2], [3, 4]])


class HugeEntries(DETERMINANT):
    sample_parameters = fixed_parameters(A=[[1000, 1, 1], [1, 1, 1], [1, 1, 2]])


class HugeAnswer(DETERMINANT):
    sample_parameters = fixed_parameters(A=[[100, 0, 0], [0, 100, 0], [0, 0, 100]])


class ZeroFirstRow(DETERMINANT):
    sample_parameters = fixed_parameters(A=[[0, 0, 0], [1, 2, 3], [4, 5, 6]])


class SingularSystem(SYSTEM):
    sample_parameters = fixed_parameters(A=[[1, 2], [2, 4]], b=[[3], [6]])


class ZeroPivotSystem(SYSTEM):
    """The family check misses a₁₁ = 0, so the elimination step itself must refuse."""

    sample_parameters = fixed_parameters(A=[[0, 1], [1, 1]], b=[[1], [2]])

    def find_parameter_problem(self, parameters: Parameters) -> None:
        return None


class DividesByZero(DETERMINANT):
    def solve(self, parameters: Parameters) -> sympy.Basic:
        return sympy.Integer(1) / (determinant_steps.cofactor_expansion(parameters["A"]) * 0)


class ReferenceUsesSteps(DETERMINANT):
    def compute_reference_answer(self, parameters: Parameters) -> sympy.Basic:
        return determinant_steps.cofactor_expansion(parameters["A"])


class ReferenceDisagrees(DETERMINANT):
    def compute_reference_answer(self, parameters: Parameters) -> sympy.Basic:
        return parameters["A"].det() + 1


class DropsMinus(DETERMINANT):
    def render_question(self, parameters: Parameters, language: contracts.Language) -> str:
        return super().render_question(parameters, language).replace("-", "")


class ShowsOtherMatrix(DETERMINANT):
    def render_question(self, parameters: Parameters, language: contracts.Language) -> str:
        return super().render_question({"A": parameters["A"] + ONES}, language)


class AsksForSecondRow(DETERMINANT):
    def render_question(self, parameters: Parameters, language: contracts.Language) -> str:
        question = super().render_question(parameters, language)
        return question.replace("першим", "другим").replace("first", "second")


class EnglishShowsOtherMatrix(DETERMINANT):
    def render_question(self, parameters: Parameters, language: contracts.Language) -> str:
        shown = parameters["A"] + ONES if language == "en" else parameters["A"]
        return super().render_question({"A": shown}, language)


class OffTemplateText(DETERMINANT):
    def render_question(self, parameters: Parameters, language: contracts.Language) -> str:
        return "Знайдіть det A." if language == "uk" else super().render_question(parameters, "en")


class SystemDropsMinus(SYSTEM):
    def render_question(self, parameters: Parameters, language: contracts.Language) -> str:
        return super().render_question(parameters, language).replace("-", "")


class WrongBySameOne(DETERMINANT):
    """Solver and reference share the same mistake; only the text reader can see it."""

    def solve(self, parameters: Parameters) -> sympy.Basic:
        return determinant_steps.cofactor_expansion(parameters["A"]) + 1

    def compute_reference_answer(self, parameters: Parameters) -> sympy.Basic:
        return parameters["A"].det() + 1


class GaussAsksForCramer(SYSTEM):
    """The program eliminates, but the text asks for Cramer's rule."""

    def render_question(self, parameters: Parameters, language: contracts.Language) -> str:
        question = super().render_question(parameters, language)
        return question.replace("методом Гаусса", "за формулами Крамера").replace(
            "by Gaussian elimination", "by Cramer's rule"
        )


class SingularCramer(CRAMER):
    sample_parameters = fixed_parameters(A=[[1, 2], [2, 4]], b=[[3], [6]])


class SingularCramerUnchecked(SingularCramer):
    """The family check misses det A = 0, so the singularity step itself must refuse."""

    def find_parameter_problem(self, parameters: Parameters) -> None:
        return None


class RepeatedEigenvalue(EIGENVALUES):
    sample_parameters = fixed_parameters(A=[[2, 0], [0, 2]])


class ComplexEigenvalues(EIGENVALUES):
    sample_parameters = fixed_parameters(A=[[0, -1], [1, 0]])


class IrrationalEigenvalues(EIGENVALUES):
    sample_parameters = fixed_parameters(A=[[1, 1], [1, 0]])


class EigenvaluesDropsMinus(EIGENVALUES):
    def render_question(self, parameters: Parameters, language: contracts.Language) -> str:
        return super().render_question(parameters, language).replace("-", "")


class BypassesSteps(DETERMINANT):
    def solve(self, parameters: Parameters) -> sympy.Basic:
        return parameters["A"].det()


@pytest.mark.parametrize(
    ("family", "reader", "stage", "reason"),
    [
        (WrongShape(), DETERMINANT_READER, "parameter_validity", "wrong_shape"),
        (HugeEntries(), DETERMINANT_READER, "parameter_validity", "number_too_large"),
        (HugeAnswer(), DETERMINANT_READER, "parameter_validity", "number_too_large"),
        (ZeroFirstRow(), DETERMINANT_READER, "parameter_validity", "degenerate_parameters"),
        (SingularSystem(), SYSTEM_READER, "parameter_validity", "answer_not_unique"),
        (ZeroPivotSystem(), SYSTEM_READER, "parameter_validity", "degenerate_parameters"),
        (DividesByZero(), DETERMINANT_READER, "parameter_validity", "division_by_zero"),
        (
            ReferenceUsesSteps(),
            DETERMINANT_READER,
            "independent_recomputation",
            "reference_uses_step_library",
        ),
        (
            ReferenceDisagrees(),
            DETERMINANT_READER,
            "independent_recomputation",
            "reference_mismatch",
        ),
        (DropsMinus(), DETERMINANT_READER, "text_program_agreement", "text_parameters_mismatch"),
        (SystemDropsMinus(), SYSTEM_READER, "text_program_agreement", "text_parameters_mismatch"),
        (
            ShowsOtherMatrix(),
            DETERMINANT_READER,
            "text_program_agreement",
            "text_parameters_mismatch",
        ),
        (AsksForSecondRow(), DETERMINANT_READER, "text_program_agreement", "text_method_mismatch"),
        (
            EnglishShowsOtherMatrix(),
            DETERMINANT_READER,
            "text_program_agreement",
            "language_mismatch",
        ),
        (OffTemplateText(), DETERMINANT_READER, "text_program_agreement", "text_unreadable"),
        (WrongBySameOne(), DETERMINANT_READER, "text_program_agreement", "text_answer_mismatch"),
        (GaussAsksForCramer(), SYSTEM_READER, "text_program_agreement", "text_method_mismatch"),
        (SingularCramer(), CRAMER_READER, "parameter_validity", "answer_not_unique"),
        (SingularCramerUnchecked(), CRAMER_READER, "parameter_validity", "degenerate_parameters"),
        (RepeatedEigenvalue(), EIGENVALUES_READER, "parameter_validity", "degenerate_parameters"),
        (ComplexEigenvalues(), EIGENVALUES_READER, "parameter_validity", "degenerate_parameters"),
        (
            IrrationalEigenvalues(),
            EIGENVALUES_READER,
            "parameter_validity",
            "degenerate_parameters",
        ),
        (
            EigenvaluesDropsMinus(),
            EIGENVALUES_READER,
            "text_program_agreement",
            "text_parameters_mismatch",
        ),
        (BypassesSteps(), DETERMINANT_READER, "concept_check", "concept_mismatch"),
    ],
    ids=lambda value: type(value).__name__ if hasattr(value, "solve") else None,
)
def test_mutant_is_rejected_with_its_reason(
    family: contracts.ItemFamily, reader: contracts.TextReader, stage: str, reason: str
) -> None:
    # Seed 0 gives matrices with negative entries, so the minus mutants change the text.
    report = pipeline.verify_variant(family, reader, 0)

    assert not report.is_accepted
    assert report.failure is not None
    assert (report.failure.stage, report.failure.reason) == (stage, reason), report.failure.detail
    assert report.failure.detail


def test_concept_mismatch_names_the_missing_concepts() -> None:
    report = pipeline.verify_variant(BypassesSteps(), DETERMINANT_READER, 0)

    assert report.failure is not None
    assert "cofactor_expansion" in report.failure.detail
    assert report.concept_check is not None
    assert report.concept_check.missing == DETERMINANT.target_concepts.concepts


def test_report_keeps_the_variant_when_the_text_check_fails() -> None:
    report = pipeline.verify_variant(AsksForSecondRow(), DETERMINANT_READER, 0)

    assert report.variant is not None
    assert "другим рядком" in report.variant.question_uk
    assert report.concept_check is None


# --- Stage 1 and the text readers on their own ---------------------------------------------------


def test_expression_too_large() -> None:
    x = sympy.Symbol("x")
    failure = parameters.find_answer_failure(sum(x**power for power in range(20)))

    assert failure is not None
    assert failure.reason == "expression_too_large"


def test_fraction_answer_passes() -> None:
    assert parameters.find_answer_failure(sympy.ImmutableMatrix([sympy.Rational(2, 5), -3])) is None


@pytest.mark.parametrize(
    ("equation", "expected"),
    [
        ("-2x + 4y = 16", ([-2, 4], 16)),
        ("x - y = 0", ([1, -1], 0)),
        ("-x = -3", ([-1, 0], -3)),
        ("3y = 9", ([0, 3], 9)),
    ],
)
def test_system_reader_reads_equations(equation: str, expected: tuple[list[int], int]) -> None:
    assert text_readers.LinearSystemTextReader._read_equation(equation) == expected


@pytest.mark.parametrize("equation", ["2x + 3x = 1", "2z + y = 1", "2x + y", "__import__('os')"])
def test_system_reader_rejects_off_template_equations(equation: str) -> None:
    with pytest.raises(ValueError):
        text_readers.LinearSystemTextReader._read_equation(equation)


def test_system_reader_rejects_an_unknown_method() -> None:
    with pytest.raises(ValueError, match="unknown method"):
        text_readers.LinearSystemTextReader("matrix_method")


class CramerOnGaussSystems(CRAMER):
    sample_parameters = SYSTEM.sample_parameters
    find_parameter_problem = SYSTEM.find_parameter_problem


def test_gauss_and_cramer_give_the_same_answer_with_different_concepts() -> None:
    gauss = pipeline.verify_variant(SYSTEM(), SYSTEM_READER, 5)
    cramer = pipeline.verify_variant(CramerOnGaussSystems(), CRAMER_READER, 5)

    assert gauss.variant is not None and cramer.variant is not None
    assert gauss.variant.parameters == cramer.variant.parameters
    assert gauss.variant.answer == cramer.variant.answer
    assert gauss.concept_check is not None and cramer.concept_check is not None
    assert gauss.concept_check.derived != cramer.concept_check.derived
