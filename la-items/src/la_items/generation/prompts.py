"""Prompt templates, kept as version-controlled files in `prompts/`, never as strings in code."""

import dataclasses
import hashlib
import inspect
import pathlib
import string
import types
import typing

from la_items.generation import targets
from la_items.steplib import determinants, eigenvalues, linear_systems

__all__ = [
    "PROMPTS_DIR",
    "PromptTemplate",
    "RenderedPrompt",
    "describe_step_library",
    "describe_text_templates",
    "load_prompt_template",
    "render_prompt",
]

PROMPTS_DIR: typing.Final = pathlib.Path(__file__).with_name("prompts")
_STEP_MODULES: typing.Final = (determinants, linear_systems, eigenvalues)


@dataclasses.dataclass(frozen=True, slots=True)
class PromptTemplate:
    """A prompt file with $placeholders, and the SHA-256 of its text."""

    name: str
    text: str
    sha256: str


@dataclasses.dataclass(frozen=True, slots=True)
class RenderedPrompt:
    """The text sent to the LLM, with the name and hash of the template it came from."""

    name: str
    template_sha256: str
    text: str


def load_prompt_template(name: str) -> PromptTemplate:
    """Read `prompts/<name>.md`.

    Parameters
    ----------
    name : str
        The file name without the extension.

    Returns
    -------
    PromptTemplate
        The template.
    """
    text = (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")
    template = PromptTemplate(name, text, hashlib.sha256(text.encode("utf-8")).hexdigest())

    return template


def render_prompt(template: PromptTemplate, values: dict[str, str]) -> RenderedPrompt:
    """Fill every $placeholder of the template.

    Parameters
    ----------
    template : PromptTemplate
        The template.
    values : dict[str, str]
        A value for every placeholder.

    Returns
    -------
    RenderedPrompt
        The prompt.

    Raises
    ------
    KeyError
        It raises when a placeholder has no value.
    """
    rendered = RenderedPrompt(
        template.name, template.sha256, string.Template(template.text).substitute(values)
    )

    return rendered


def _describe_step(module: types.ModuleType, function_name: str) -> str:
    function = getattr(module, function_name)
    signature = inspect.signature(function)
    parameters = ", ".join(signature.parameters)
    summary = (inspect.getdoc(function) or "").splitlines()[0]
    module_name = module.__name__.rsplit(".", 1)[-1]
    description = (
        f"- `{module_name}.{function_name}({parameters})` records `{function.concept}`. {summary}"
    )

    return description


def describe_step_library() -> str:
    """List every library step with its module, parameters, concept and summary.

    Returns
    -------
    str
        One Markdown bullet per step.
    """
    description = "\n".join(
        _describe_step(module, name)
        for module in _STEP_MODULES
        for name in module.__all__
        if hasattr(getattr(module, name), "concept")
    )

    return description


def describe_text_templates(target: targets.SupportedTarget) -> str:
    """Show the sentence form of the target's example family, rendered for seed 0.

    Parameters
    ----------
    target : targets.SupportedTarget
        The supported target.

    Returns
    -------
    str
        The Ukrainian and the English example question.
    """
    family = target.example_family()
    parameters = family.sample_parameters(0)
    examples = (
        f'- uk: "{family.render_question(parameters, "uk")}"\n'
        f'- en: "{family.render_question(parameters, "en")}"'
    )

    return examples
