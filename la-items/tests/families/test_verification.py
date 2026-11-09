import collections.abc

import pytest
import sympy

from la_items import contracts
from la_items.families import determinants, linear_systems, verification

FAMILIES = [
    determinants.Determinant3x3CofactorRow1(),
    linear_systems.Solve2x2LinearSystemGaussian(),
]
SEEDS = range(200)


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.name)
def test_every_seed_matches_reference_and_target(family: contracts.ItemFamily) -> None:
    for seed in SEEDS:
        variant, check = verification.build_variant(family, seed)

        assert check.is_accepted, (seed, check.missing, check.extra)
        assert variant.answer == family.compute_reference_answer(variant.parameters)


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.name)
def test_same_seed_gives_same_variant(family: contracts.ItemFamily) -> None:
    first, _ = verification.build_variant(family, 7)
    second, _ = verification.build_variant(family, 7)

    assert first == second


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.name)
def test_both_languages_show_the_same_numbers(family: contracts.ItemFamily) -> None:
    variant, _ = verification.build_variant(family, 3)

    def numbers(text: str) -> list[str]:
        return [token.strip(".,;[]()") for token in text.split() if any(c.isdigit() for c in token)]

    assert variant.question_uk != variant.question_en
    assert numbers(variant.question_uk) == numbers(variant.question_en)


def test_determinant_question_names_the_method() -> None:
    variant, _ = verification.build_variant(determinants.Determinant3x3CofactorRow1(), 0)

    assert "розкладом за першим рядком" in variant.question_uk
    assert "cofactor expansion along the first row" in variant.question_en


def test_determinant_variant_matches_sympy_det() -> None:
    variant, _ = verification.build_variant(determinants.Determinant3x3CofactorRow1(), 11)

    assert variant.answer == variant.parameters["A"].det()  # type: ignore[attr-defined]


class SolvesWithoutSteps(determinants.Determinant3x3CofactorRow1):
    def solve(self, parameters: collections.abc.Mapping[str, sympy.Basic]) -> sympy.Basic:
        return parameters["A"].det()  # type: ignore[attr-defined,no-any-return]


class GivesWrongAnswer(determinants.Determinant3x3CofactorRow1):
    def compute_reference_answer(
        self, parameters: collections.abc.Mapping[str, sympy.Basic]
    ) -> sympy.Basic:
        return sympy.Integer(10**9)


def test_solution_bypassing_step_library_is_rejected() -> None:
    _, check = verification.build_variant(SolvesWithoutSteps(), 0)

    assert not check.is_accepted
    assert check.missing == SolvesWithoutSteps.target_concepts.concepts


def test_answer_mismatch_raises() -> None:
    with pytest.raises(verification.AnswerMismatch, match="seed 0"):
        verification.build_variant(GivesWrongAnswer(), 0)
