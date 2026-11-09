"""Build a variant from any item family and run the checks every family must pass."""

from la_items import contracts
from la_items.steplib import trace

__all__ = ["AnswerMismatch", "build_variant"]


class AnswerMismatch(AssertionError):
    pass


def build_variant(
    family: contracts.ItemFamily, seed: int
) -> tuple[contracts.Variant, contracts.ConceptCheck]:
    """Sample, render, solve and check one variant of a family.

    Parameters
    ----------
    family : contracts.ItemFamily
        The family to run.
    seed : int
        The seed of the variant.

    Returns
    -------
    tuple[contracts.Variant, contracts.ConceptCheck]
        The variant, and the comparison of the family's target concepts with the concepts its
        solution executed. The caller accepts the variant only when the check is accepted.

    Raises
    ------
    AnswerMismatch
        It raises when the step-library answer differs from the independent one.
    """
    parameters = family.sample_parameters(seed)

    with trace.recording() as recorded:
        answer = family.solve(parameters)

    reference_answer = family.compute_reference_answer(parameters)
    if answer != reference_answer:
        raise AnswerMismatch(
            f"{family.name} seed {seed}: step library gave {answer}, reference gave"
            f" {reference_answer}"
        )

    variant = contracts.Variant(
        seed=seed,
        parameters=parameters,
        question_uk=family.render_question(parameters, "uk"),
        question_en=family.render_question(parameters, "en"),
        answer=answer,
    )
    check = contracts.ConceptCheck(
        requested=family.target_concepts,
        derived=contracts.ConceptVector.from_trace(recorded),
    )
    variant_and_check = variant, check

    return variant_and_check
