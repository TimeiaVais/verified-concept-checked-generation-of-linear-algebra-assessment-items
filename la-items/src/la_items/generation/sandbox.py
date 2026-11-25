"""Run generated family code in a separate process with a time limit.

The child is `python -I -m la_items.generation.sandbox_runner`: isolated mode, an empty
environment, a fresh temporary directory, a wall-clock timeout and a CPU-time limit.
"""

import collections.abc
import dataclasses
import json
import resource
import subprocess
import sys
import tempfile

from la_items import contracts

__all__ = ["FamilyCheck", "check_family_in_sandbox"]


@dataclasses.dataclass(frozen=True, slots=True)
class FamilyCheck:
    """The verification of one generated family over many seeds."""

    family_name: str | None
    passed_seeds: int
    total_seeds: int
    failing_seed: int | None
    failure: contracts.CheckFailure | None

    @property
    def is_accepted(self) -> bool:
        """Whether every seed passed every stage."""
        is_accepted = self.failure is None

        return is_accepted


def _execution_failure(reason: contracts.Reason, detail: str, total_seeds: int) -> FamilyCheck:
    family_check = FamilyCheck(
        None, 0, total_seeds, None, contracts.CheckFailure("execution", reason, detail)
    )

    return family_check


def check_family_in_sandbox(
    source: str,
    requested_concepts: frozenset[str],
    seeds: collections.abc.Sequence[int],
    timeout_seconds: float,
) -> FamilyCheck:
    """Verify generated code on every seed in a child process.

    shortcut: no network or file access is enforced by the static check, not by the operating
    system; add an OS sandbox (a container or seccomp) before running untrusted models unattended.

    Parameters
    ----------
    source : str
        Generated code that passed the static check.
    requested_concepts : frozenset[str]
        The target the family was generated for.
    seeds : Sequence[int]
        The seeds to verify.
    timeout_seconds : float
        The wall-clock limit for the whole run.

    Returns
    -------
    FamilyCheck
        The result; a timeout or a crash of the child is an "execution" failure.
    """
    request = json.dumps(
        {"source": source, "requested_concepts": sorted(requested_concepts), "seeds": list(seeds)}
    )
    cpu_seconds = int(timeout_seconds) + 1

    def limit_cpu_time() -> None:
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))

    with tempfile.TemporaryDirectory() as workdir:
        try:
            completed = subprocess.run(
                [sys.executable, "-I", "-m", "la_items.generation.sandbox_runner"],
                input=request,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=workdir,
                env={},
                preexec_fn=limit_cpu_time,
                check=False,
            )

            if completed.returncode != 0:
                stderr_lines = completed.stderr.strip().splitlines() or ["no error output"]
                family_check = _execution_failure(
                    "crashed",
                    f"exit code {completed.returncode}: {stderr_lines[-1]}",
                    len(seeds),
                )

            else:
                summary = json.loads(completed.stdout)
                failure = summary["failure"]
                family_check = FamilyCheck(
                    summary["family_name"],
                    summary["passed_seeds"],
                    summary["total_seeds"],
                    summary["failing_seed"],
                    None if failure is None else contracts.CheckFailure(**failure),
                )

        except subprocess.TimeoutExpired:
            family_check = _execution_failure(
                "timeout", f"no result within {timeout_seconds} s", len(seeds)
            )

    return family_check
