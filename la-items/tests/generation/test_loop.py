import inspect
import json
import pathlib

import pytest

from la_items import contracts
from la_items.families import determinants, linear_systems
from la_items.generation import llm, loop

DETERMINANT_SOURCE = inspect.getsource(determinants)
TARGET = determinants.Determinant3x3CofactorRow1.target_concepts
SEEDS = range(5)


def reply_with(source: str) -> str:
    return f"Here is the module.\n\n```python\n{source}```\n"


def logged_client(tmp_path: pathlib.Path, replies: list[str]) -> llm.LoggedLlmClient:
    files = []

    for number, reply in enumerate(replies, start=1):
        path = tmp_path / f"reply_{number}.md"
        path.write_text(reply, encoding="utf-8")
        files.append(path)

    return llm.LoggedLlmClient(
        llm.FileReplayClient(files, "test-model", "1"), tmp_path / "llm_calls.jsonl"
    )


def logged_calls(client: llm.LoggedLlmClient) -> list[dict[str, object]]:
    return [json.loads(line) for line in client.log_path.read_text(encoding="utf-8").splitlines()]


@pytest.mark.slow
def test_correct_family_is_accepted_and_saved(tmp_path: pathlib.Path) -> None:
    client = logged_client(tmp_path, [reply_with(DETERMINANT_SOURCE)])

    result = loop.generate_family(TARGET, client, seeds=SEEDS)
    family_dir = loop.save_generated_family(result, tmp_path / "generated")

    assert result.accepted is not None and result.accepted.number == 1
    assert (family_dir / "family.py").read_text(encoding="utf-8") == DETERMINANT_SOURCE
    record = json.loads((family_dir / "generation.json").read_text(encoding="utf-8"))
    assert record["family_name"] == "determinant_3x3_cofactor_row_1"
    assert record["model"] == "test-model" and record["prompt_sha256"] == result.prompt_sha256
    assert record["attempts"] == [{"number": 1, "stage": None, "reason": None, "detail": None}]
    assert len(logged_calls(client)) == 1


@pytest.mark.slow
def test_failure_is_fed_back_and_the_fix_is_accepted(tmp_path: pathlib.Path) -> None:
    client = logged_client(
        tmp_path, [reply_with("import os\n" + DETERMINANT_SOURCE), reply_with(DETERMINANT_SOURCE)]
    )

    result = loop.generate_family(TARGET, client, seeds=SEEDS)

    first, second = result.attempts
    assert first.failure is not None and first.failure.reason == "forbidden_import"
    assert second.failure is None and result.accepted is second
    first_prompt, second_prompt = (call["prompt"] for call in logged_calls(client))
    assert "first attempt" in str(first_prompt)
    assert "reason: forbidden_import" in str(second_prompt)


def test_reply_without_code_is_rejected(tmp_path: pathlib.Path) -> None:
    client = logged_client(tmp_path, ["I cannot help with that."])

    result = loop.generate_family(TARGET, client, max_attempts=1, seeds=SEEDS)

    assert result.accepted is None
    assert result.attempts[0].failure == contracts.CheckFailure(
        "static_check", "missing_family", "the reply has no ```python block"
    )


@pytest.mark.slow
def test_endless_loop_times_out(tmp_path: pathlib.Path) -> None:
    hanging = DETERMINANT_SOURCE.replace(
        "        rng = random.Random(seed)", "        while True:\n            pass"
    )
    client = logged_client(tmp_path, [reply_with(hanging)])

    result = loop.generate_family(TARGET, client, max_attempts=1, seeds=SEEDS, timeout_seconds=8)

    failure = result.attempts[0].failure
    assert failure is not None and (failure.stage, failure.reason) == ("execution", "timeout")


@pytest.mark.slow
def test_family_declaring_another_target_is_rejected(tmp_path: pathlib.Path) -> None:
    client = logged_client(tmp_path, [reply_with(DETERMINANT_SOURCE)])
    cramer = linear_systems.Solve2x2LinearSystemCramer.target_concepts

    result = loop.generate_family(cramer, client, max_attempts=1, seeds=SEEDS)

    failure = result.attempts[0].failure
    assert failure is not None and failure.reason == "concept_mismatch"
    assert "declares" in failure.detail


@pytest.mark.slow
def test_runtime_error_in_generated_code_is_a_crash(tmp_path: pathlib.Path) -> None:
    broken = DETERMINANT_SOURCE.replace('rows = parameters["A"].tolist()', 'rows = parameters["X"]')
    client = logged_client(tmp_path, [reply_with(broken)])

    result = loop.generate_family(TARGET, client, max_attempts=1, seeds=SEEDS)

    failure = result.attempts[0].failure
    assert failure is not None and (failure.stage, failure.reason) == ("execution", "crashed")
    assert "KeyError" in failure.detail


def test_unsupported_target_is_refused_before_any_call(tmp_path: pathlib.Path) -> None:
    client = logged_client(tmp_path, [reply_with(DETERMINANT_SOURCE)])

    with pytest.raises(ValueError, match="no text reader"):
        loop.generate_family(contracts.ConceptVector(frozenset({"matrix_mult"})), client)

    assert not client.log_path.exists()


def test_saving_without_an_accepted_attempt_fails(tmp_path: pathlib.Path) -> None:
    client = logged_client(tmp_path, ["no code"])
    result = loop.generate_family(TARGET, client, max_attempts=1, seeds=SEEDS)

    with pytest.raises(ValueError, match="no accepted attempt"):
        loop.save_generated_family(result, tmp_path / "generated")
