import json
import pathlib

import pytest

from la_items.generation import llm, prompts, targets

SRC = pathlib.Path(prompts.__file__).parents[1]


def test_replay_client_returns_files_in_order(tmp_path: pathlib.Path) -> None:
    files = [tmp_path / "1.md", tmp_path / "2.md"]
    files[0].write_text("first", encoding="utf-8")
    files[1].write_text("second", encoding="utf-8")
    client = llm.FileReplayClient(files, model="some-chat-model", model_version="2026-11")

    first = client.complete("prompt", {})
    second = client.complete("prompt", {})

    assert (first.text, second.text) == ("first", "second")
    assert (first.model, first.model_version) == ("some-chat-model", "2026-11")
    with pytest.raises(RuntimeError, match="no saved reply"):
        client.complete("prompt", {})


def test_logged_client_records_every_field(tmp_path: pathlib.Path) -> None:
    reply = tmp_path / "reply.md"
    reply.write_text("the reply", encoding="utf-8")
    log_path = tmp_path / "results" / "llm_calls" / "run.jsonl"
    client = llm.LoggedLlmClient(llm.FileReplayClient([reply], "m", "v1"), log_path)
    prompt = prompts.RenderedPrompt("generate_family", "abc123", "the full prompt")

    client.complete(prompt, {"temperature": 0.2})

    (line,) = log_path.read_text(encoding="utf-8").splitlines()
    call = json.loads(line)
    assert call["model"] == "m" and call["model_version"] == "v1"
    assert call["parameters"] == {"temperature": 0.2}
    assert call["prompt_name"] == "generate_family" and call["prompt_sha256"] == "abc123"
    assert call["prompt"] == "the full prompt" and call["response"] == "the reply"
    assert call["timestamp"]


def test_prompt_renders_with_every_placeholder_filled() -> None:
    template = prompts.load_prompt_template("generate_family")
    target = targets.SUPPORTED_TARGETS[0]

    rendered = prompts.render_prompt(
        template,
        {
            "target_concepts": "- `det_2x2`",
            "step_library": prompts.describe_step_library(),
            "text_templates": prompts.describe_text_templates(target),
            "feedback": "None",
        },
    )

    assert "$" not in rendered.text.replace("$target", "")
    assert "determinants.cofactor_expansion(matrix)" in rendered.text
    assert "розкладом за першим рядком" in rendered.text
    assert rendered.template_sha256 == template.sha256


def test_step_library_description_lists_every_step() -> None:
    description = prompts.describe_step_library()

    assert len(description.splitlines()) == 20
    assert "records `cramer_rule`" in description


def test_prompts_live_in_files_not_in_code() -> None:
    template_text = prompts.load_prompt_template("generate_family").text
    first_sentence = template_text.splitlines()[0]

    assert list(prompts.PROMPTS_DIR.glob("*.md"))
    assert not [
        path for path in SRC.rglob("*.py") if first_sentence in path.read_text(encoding="utf-8")
    ]


def test_every_supported_target_has_a_reader_and_an_example() -> None:
    for target in targets.SUPPORTED_TARGETS:
        assert targets.find_supported_target(target.concepts) is target
        assert target.make_reader().expected_method
