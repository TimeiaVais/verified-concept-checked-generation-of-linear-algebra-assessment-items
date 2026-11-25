"""The repair loop: ask the LLM for a family, check it, and return the failure until it passes."""

import collections.abc
import dataclasses
import json
import pathlib
import re
import typing

from la_items import contracts
from la_items.generation import llm, prompts, sandbox, static_check, targets

__all__ = [
    "GenerationAttempt",
    "GenerationResult",
    "extract_code",
    "format_feedback",
    "generate_family",
    "save_generated_family",
]

PROMPT_NAME: typing.Final = "generate_family"
_FIRST_ATTEMPT: typing.Final = "None, this is the first attempt."


@dataclasses.dataclass(frozen=True, slots=True)
class GenerationAttempt:
    """One LLM reply and what the checks found in it."""

    number: int
    source: str | None
    family_check: sandbox.FamilyCheck | None
    failure: contracts.CheckFailure | None
    model: str
    model_version: str


@dataclasses.dataclass(frozen=True, slots=True)
class GenerationResult:
    """The outcome of the repair loop for one target."""

    target_concepts: frozenset[str]
    prompt_name: str
    prompt_sha256: str
    seeds: tuple[int, ...]
    attempts: tuple[GenerationAttempt, ...]

    @property
    def accepted(self) -> GenerationAttempt | None:
        """The attempt that passed every check, or None."""
        passed = [attempt for attempt in self.attempts if attempt.failure is None]
        accepted = passed[0] if passed else None

        return accepted


def extract_code(reply: str) -> str | None:
    """Return the first ```python block of the reply, or None."""
    match = re.search(r"```python\n(.*?)```", reply, re.S)
    code = None if match is None else match.group(1)

    return code


def format_feedback(failure: contracts.CheckFailure, failing_seed: int | None) -> str:
    """Describe a failure for the next prompt: stage, reason code, seed and details."""
    seed_line = "" if failing_seed is None else f"\n- seed: {failing_seed}"
    feedback = (
        "The previous module was rejected. Fix this and return the whole module again.\n"
        f"- stage: {failure.stage}\n- reason: {failure.reason}{seed_line}\n"
        f"- detail: {failure.detail}"
    )

    return feedback


def _check_reply(
    reply: str, target: frozenset[str], seeds: tuple[int, ...], timeout_seconds: float
) -> tuple[str | None, sandbox.FamilyCheck | None, contracts.CheckFailure | None]:
    source = extract_code(reply)
    family_check = None

    if source is None:
        failure: contracts.CheckFailure | None = contracts.CheckFailure(
            "static_check", "missing_family", "the reply has no ```python block"
        )

    else:
        failure = static_check.find_static_failure(source)

        if failure is None:
            family_check = sandbox.check_family_in_sandbox(source, target, seeds, timeout_seconds)
            failure = family_check.failure

    checked = source, family_check, failure

    return checked


def generate_family(
    target_concepts: contracts.ConceptVector,
    client: llm.LoggedLlmClient,
    *,
    max_attempts: int = 3,
    seeds: collections.abc.Iterable[int] = range(50),
    timeout_seconds: float = 120,
    llm_parameters: collections.abc.Mapping[str, object] | None = None,
) -> GenerationResult:
    """Generate a family for the target, feeding each failure back, up to `max_attempts` times.

    Parameters
    ----------
    target_concepts : contracts.ConceptVector
        The concepts the family must require.
    client : llm.LoggedLlmClient
        The client; every call is logged.
    max_attempts : int
        The number of LLM replies to try.
    seeds : Iterable[int]
        The seeds each reply is verified on.
    timeout_seconds : float
        The sandbox time limit for one reply.
    llm_parameters : Mapping[str, object] | None
        Call parameters passed to the model and logged, for example temperature.

    Returns
    -------
    GenerationResult
        All attempts; `accepted` is the one that passed, if any.

    Raises
    ------
    ValueError
        It raises when generation does not support the target, before any LLM call.
    """
    target = targets.find_supported_target(target_concepts.concepts)
    if target is None:
        raise ValueError(f"no text reader for target {sorted(target_concepts.concepts)}")
    template = prompts.load_prompt_template(PROMPT_NAME)
    seed_list = tuple(seeds)
    fixed_values = {
        "target_concepts": "\n".join(f"- `{concept}`" for concept in sorted(target.concepts)),
        "step_library": prompts.describe_step_library(),
        "text_templates": prompts.describe_text_templates(target),
    }
    attempts: list[GenerationAttempt] = []
    feedback = _FIRST_ATTEMPT

    for number in range(1, max_attempts + 1):
        if not attempts or attempts[-1].failure is not None:
            prompt = prompts.render_prompt(template, {**fixed_values, "feedback": feedback})
            response = client.complete(prompt, llm_parameters or {})
            source, family_check, failure = _check_reply(
                response.text, target.concepts, seed_list, timeout_seconds
            )
            attempts.append(
                GenerationAttempt(
                    number, source, family_check, failure, response.model, response.model_version
                )
            )

            if failure is not None:
                failing_seed = None if family_check is None else family_check.failing_seed
                feedback = format_feedback(failure, failing_seed)

    result = GenerationResult(
        target.concepts, template.name, template.sha256, seed_list, tuple(attempts)
    )

    return result


def save_generated_family(result: GenerationResult, output_dir: pathlib.Path) -> pathlib.Path:
    """Save the accepted family's code and the record of how it was produced.

    Parameters
    ----------
    result : GenerationResult
        A result with an accepted attempt.
    output_dir : pathlib.Path
        The `generated/` folder.

    Returns
    -------
    pathlib.Path
        The family's folder, `output_dir / <family name>`.

    Raises
    ------
    ValueError
        It raises when no attempt was accepted.
    """
    accepted = result.accepted
    if accepted is None or accepted.source is None or accepted.family_check is None:
        raise ValueError("no accepted attempt to save")
    family_dir = output_dir / str(accepted.family_check.family_name)
    family_dir.mkdir(parents=True, exist_ok=True)
    (family_dir / "family.py").write_text(accepted.source, encoding="utf-8")
    record = {
        "family_name": accepted.family_check.family_name,
        "target_concepts": sorted(result.target_concepts),
        "model": accepted.model,
        "model_version": accepted.model_version,
        "prompt_name": result.prompt_name,
        "prompt_sha256": result.prompt_sha256,
        "seeds": list(result.seeds),
        "attempts": [
            {
                "number": attempt.number,
                "stage": None if attempt.failure is None else attempt.failure.stage,
                "reason": None if attempt.failure is None else attempt.failure.reason,
                "detail": None if attempt.failure is None else attempt.failure.detail,
            }
            for attempt in result.attempts
        ],
    }
    (family_dir / "generation.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    return family_dir
