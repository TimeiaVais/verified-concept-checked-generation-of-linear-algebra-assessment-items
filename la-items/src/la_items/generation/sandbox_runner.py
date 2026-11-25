"""Child-process side of the sandbox: run generated family code through the verification pipeline.

`sandbox.check_family_in_sandbox` starts this module with `python -I -m`, writes a JSON request
to stdin and reads a JSON summary from stdout. The generated code runs only in this process.
"""

import ast
import json
import sys
import traceback
import typing

from la_items.generation import static_check, targets
from la_items.verification import pipeline

__all__ = ["check_family_source", "main"]


def _summarise(
    family_name: str | None,
    passed: int,
    total: int,
    failing_seed: int | None,
    stage: str | None,
    reason: str | None,
    detail: str | None,
) -> dict[str, typing.Any]:
    failure = None if stage is None else {"stage": stage, "reason": reason, "detail": detail}
    summary = {
        "family_name": family_name,
        "passed_seeds": passed,
        "total_seeds": total,
        "failing_seed": failing_seed,
        "failure": failure,
    }

    return summary


def check_family_source(
    source: str, requested_concepts: list[str], seeds: list[int]
) -> dict[str, typing.Any]:
    """Run the generated family on every seed and summarise the first failure.

    Parameters
    ----------
    source : str
        Generated code that passed the static check.
    requested_concepts : list[str]
        The target the family was generated for.
    seeds : list[int]
        The seeds to verify.

    Returns
    -------
    dict[str, Any]
        The summary that `sandbox.check_family_in_sandbox` reads.
    """
    family_class = static_check.find_family_class(ast.parse(source))
    namespace: dict[str, typing.Any] = {"__name__": "generated_family"}
    exec(compile(source, "<generated family>", "exec"), namespace)  # noqa: S102
    family = namespace[family_class.name]()  # type: ignore[union-attr]
    declared = family.target_concepts.concepts
    supported_target = targets.find_supported_target(declared)

    if declared != frozenset(requested_concepts):
        summary = _summarise(
            family.name,
            0,
            len(seeds),
            None,
            "concept_check",
            "concept_mismatch",
            f"the family declares {sorted(declared)}, the request was {sorted(requested_concepts)}",
        )

    elif supported_target is None:
        summary = _summarise(
            family.name,
            0,
            len(seeds),
            None,
            "text_program_agreement",
            "no_text_reader",
            f"no text reader for {sorted(declared)}",
        )

    else:
        reports = pipeline.verify_family(family, supported_target.make_reader(), seeds)
        failed = [report for report in reports if not report.is_accepted]
        first = failed[0] if failed else None
        summary = _summarise(
            family.name,
            len(reports) - len(failed),
            len(reports),
            None if first is None else first.seed,
            None if first is None or first.failure is None else first.failure.stage,
            None if first is None or first.failure is None else first.failure.reason,
            None if first is None or first.failure is None else first.failure.detail,
        )

    return summary


def main() -> None:
    """Read the request from stdin and write the summary to stdout."""
    request = json.loads(sys.stdin.read())

    try:
        summary = check_family_source(
            request["source"], request["requested_concepts"], request["seeds"]
        )

    # Any error raised by generated code is the result being reported, not a crash of the check.
    except Exception:
        last_line = traceback.format_exc().strip().splitlines()[-1]
        summary = _summarise(
            None, 0, len(request["seeds"]), None, "execution", "crashed", last_line
        )

    sys.stdout.write(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
