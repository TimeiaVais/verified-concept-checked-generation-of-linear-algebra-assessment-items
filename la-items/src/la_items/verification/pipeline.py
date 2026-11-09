"""The verification pipeline: four stages, in order, for each seed of a family.

1. Parameter validity: shapes, size, the family's degenerate cases, and the answer's size.
2. Independent recomputation: a reference that shares no code with the step library.
3. Text-program agreement: a reader that sees only the text must find the same item.
4. Concept check: the executed steps must give exactly the target concepts.

The pipeline stops at the first failure; later stages rely on the earlier ones.
"""

import collections.abc

import sympy

from la_items import contracts
from la_items.steplib import trace
from la_items.verification import parameters as parameter_checks

__all__ = ["verify_family", "verify_variant"]

_LANGUAGES: tuple[contracts.Language, ...] = ("uk", "en")


def _solve_with_steps(
    family: contracts.ItemFamily, parameters: collections.abc.Mapping[str, sympy.Basic]
) -> tuple[sympy.Basic | None, list[str], contracts.CheckFailure | None]:
    answer = None
    failure = None

    with trace.recording() as recorded:
        try:
            answer = family.solve(parameters)

        except ZeroDivisionError as error:
            failure = contracts.CheckFailure("parameter_validity", "division_by_zero", str(error))

        # A library step raises ValueError on a case it does not handle, such as a zero pivot.
        except ValueError as error:
            failure = contracts.CheckFailure(
                "parameter_validity", "degenerate_parameters", str(error)
            )

    if failure is None and answer is not None:
        failure = parameter_checks.find_answer_failure(answer)

    solution = answer, recorded, failure

    return solution


def _find_recomputation_failure(
    family: contracts.ItemFamily,
    parameters: collections.abc.Mapping[str, sympy.Basic],
    answer: sympy.Basic,
) -> contracts.CheckFailure | None:
    with trace.recording() as recorded:
        reference_answer = family.compute_reference_answer(parameters)

    if recorded:
        failure: contracts.CheckFailure | None = contracts.CheckFailure(
            "independent_recomputation",
            "reference_uses_step_library",
            f"the reference called steps for {sorted(set(recorded))}",
        )

    elif reference_answer != answer:
        failure = contracts.CheckFailure(
            "independent_recomputation",
            "reference_mismatch",
            f"step library gave {answer}, reference gave {reference_answer}",
        )

    else:
        failure = None

    return failure


def _find_text_failure(
    reader: contracts.TextReader,
    questions: collections.abc.Mapping[contracts.Language, str],
    parameters: collections.abc.Mapping[str, sympy.Basic],
    answer: sympy.Basic,
) -> contracts.CheckFailure | None:
    readings: dict[contracts.Language, contracts.TextReading] = {}
    failure = None

    for language in _LANGUAGES:
        try:
            readings[language] = reader.read_question(questions[language], language)

        except ValueError as error:
            failure = contracts.CheckFailure(
                "text_program_agreement", "text_unreadable", f"{language}: {error}"
            )

    if failure is None:
        uk_reading, en_reading = readings["uk"], readings["en"]
        wrong_parameters = sorted(
            name for name in parameters if uk_reading.parameters.get(name) != parameters[name]
        )

        if (uk_reading.parameters, uk_reading.method) != (en_reading.parameters, en_reading.method):
            failure = contracts.CheckFailure(
                "text_program_agreement",
                "language_mismatch",
                f"uk reads {dict(uk_reading.parameters)}, {uk_reading.method}; "
                f"en reads {dict(en_reading.parameters)}, {en_reading.method}",
            )

        elif wrong_parameters or set(uk_reading.parameters) != set(parameters):
            failure = contracts.CheckFailure(
                "text_program_agreement",
                "text_parameters_mismatch",
                f"text shows {dict(uk_reading.parameters)}, program has {dict(parameters)}",
            )

        elif uk_reading.method != reader.expected_method:
            failure = contracts.CheckFailure(
                "text_program_agreement",
                "text_method_mismatch",
                f"text asks for {uk_reading.method}, the family requires {reader.expected_method}",
            )

        elif uk_reading.answer != answer:
            failure = contracts.CheckFailure(
                "text_program_agreement",
                "text_answer_mismatch",
                f"text solver gave {uk_reading.answer}, program gave {answer}",
            )

    return failure


def verify_variant(
    family: contracts.ItemFamily, reader: contracts.TextReader, seed: int
) -> contracts.VerificationReport:
    """Run the four stages for one seed and report the first failure, if any.

    Parameters
    ----------
    family : contracts.ItemFamily
        The family to check.
    reader : contracts.TextReader
        The text reader written for this family.
    seed : int
        The seed of the variant.

    Returns
    -------
    contracts.VerificationReport
        The report. `is_accepted` is True only when all four stages pass.
    """
    parameters = family.sample_parameters(seed)
    answer: sympy.Basic | None = None
    recorded: list[str] = []
    variant = None
    concept_check = None
    failure = parameter_checks.find_parameter_failure(family, parameters)

    if failure is None:
        answer, recorded, failure = _solve_with_steps(family, parameters)

    if failure is None and answer is not None:
        failure = _find_recomputation_failure(family, parameters, answer)

    if failure is None and answer is not None:
        questions = {
            language: family.render_question(parameters, language) for language in _LANGUAGES
        }
        variant = contracts.Variant(
            seed=seed,
            parameters=parameters,
            question_uk=questions["uk"],
            question_en=questions["en"],
            answer=answer,
        )
        failure = _find_text_failure(reader, questions, parameters, answer)

    if failure is None:
        concept_check = contracts.ConceptCheck(
            requested=family.target_concepts,
            derived=contracts.ConceptVector.from_trace(recorded),
        )
        if not concept_check.is_accepted:
            failure = contracts.CheckFailure(
                "concept_check",
                "concept_mismatch",
                f"missing {sorted(concept_check.missing)}, extra {sorted(concept_check.extra)}",
            )

    report = contracts.VerificationReport(
        family_name=family.name,
        seed=seed,
        variant=variant,
        concept_check=concept_check,
        failure=failure,
    )

    return report


def verify_family(
    family: contracts.ItemFamily,
    reader: contracts.TextReader,
    seeds: collections.abc.Iterable[int],
) -> list[contracts.VerificationReport]:
    """Run `verify_variant` for every seed.

    Parameters
    ----------
    family : contracts.ItemFamily
        The family to check.
    reader : contracts.TextReader
        The text reader written for this family.
    seeds : Iterable[int]
        The seeds to check.

    Returns
    -------
    list[contracts.VerificationReport]
        One report per seed, in seed order.
    """
    reports = [verify_variant(family, reader, seed) for seed in seeds]

    return reports
