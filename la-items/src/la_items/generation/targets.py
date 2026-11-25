"""The targets that generation supports: those with a hand-written example and a text reader.

A generated family is checked by the text reader of its target, and the prompt shows the sentence
form of the matching hand-written family. A target without both cannot be generated yet.
"""

import collections.abc
import dataclasses
import typing

from la_items import contracts
from la_items.families import determinants, eigenvalues, linear_systems
from la_items.verification import text_readers

__all__ = ["SUPPORTED_TARGETS", "SupportedTarget", "find_supported_target"]


@dataclasses.dataclass(frozen=True, slots=True)
class SupportedTarget:
    """One target concept vector, with its example family and its text reader."""

    example_family: type[contracts.ItemFamily]
    make_reader: collections.abc.Callable[[], contracts.TextReader]

    @property
    def concepts(self) -> frozenset[str]:
        """The target concepts, taken from the example family."""
        concepts = self.example_family().target_concepts.concepts

        return concepts


SUPPORTED_TARGETS: typing.Final = (
    SupportedTarget(
        determinants.Determinant3x3CofactorRow1, text_readers.DeterminantCofactorTextReader
    ),
    SupportedTarget(
        linear_systems.Solve2x2LinearSystemGaussian,
        lambda: text_readers.LinearSystemTextReader("gaussian_elimination"),
    ),
    SupportedTarget(
        linear_systems.Solve2x2LinearSystemCramer,
        lambda: text_readers.LinearSystemTextReader("cramer_rule"),
    ),
    SupportedTarget(
        eigenvalues.Eigenvalues2x2CharacteristicPolynomial, text_readers.EigenvaluesTextReader
    ),
)


def find_supported_target(concepts: frozenset[str]) -> SupportedTarget | None:
    """Return the supported target with exactly these concepts, or None.

    Parameters
    ----------
    concepts : frozenset[str]
        The target concepts.

    Returns
    -------
    SupportedTarget | None
        The match, or None when generation does not support this target.
    """
    matches = [target for target in SUPPORTED_TARGETS if target.concepts == concepts]
    supported_target = matches[0] if matches else None

    return supported_target
