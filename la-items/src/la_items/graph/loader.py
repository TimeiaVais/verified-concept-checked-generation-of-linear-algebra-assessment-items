"""Load the concept graph and check its integrity."""

import dataclasses
import pathlib
import typing

import yaml

__all__ = ["BLOCKS", "GRAPH_PATH", "Concept", "GraphError", "load_graph"]

GRAPH_PATH: typing.Final = pathlib.Path(__file__).with_name("concepts.yaml")
BLOCKS: typing.Final = frozenset({"linear_systems", "matrices", "determinants", "eigenvalues"})


class GraphError(ValueError):
    pass


@dataclasses.dataclass(frozen=True, slots=True)
class Concept:
    """One node of the concept graph, as written in ``concepts.yaml``."""

    id: str
    name_uk: str
    name_en: str
    block: str
    prerequisites: tuple[str, ...]
    source: str


def load_graph(path: pathlib.Path = GRAPH_PATH) -> dict[str, Concept]:
    """Read the graph file and check it.

    Parameters
    ----------
    path : pathlib.Path
        The YAML file with a ``concepts`` list.

    Returns
    -------
    dict[str, Concept]
        The concepts by id, in file order.

    Raises
    ------
    GraphError
        It raises on a duplicate id, an unknown block, an unknown or self prerequisite, or a cycle.
    """
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    graph: dict[str, Concept] = {}

    for item in raw["concepts"]:
        concept = Concept(
            id=item["id"],
            name_uk=item["name_uk"],
            name_en=item["name_en"],
            block=item["block"],
            prerequisites=tuple(item["prerequisites"]),
            source=item["source"],
        )
        if concept.id in graph:
            raise GraphError(f"duplicate concept id: {concept.id}")
        if concept.block not in BLOCKS:
            raise GraphError(f"{concept.id}: unknown block {concept.block!r}")
        graph[concept.id] = concept

    _check_prerequisites(graph)
    _check_acyclic(graph)

    return graph


def _check_prerequisites(graph: dict[str, Concept]) -> None:
    for concept in graph.values():
        for prereq in concept.prerequisites:
            if prereq not in graph:
                raise GraphError(f"{concept.id}: unknown prerequisite {prereq!r}")
            if prereq == concept.id:
                raise GraphError(f"{concept.id}: concept is its own prerequisite")


def _check_acyclic(graph: dict[str, Concept]) -> None:
    done: set[str] = set()
    on_path: list[str] = []

    # Nested so the depth-first walk shares `done` and `on_path` without passing them down.
    def visit(concept_id: str) -> None:
        if concept_id in on_path:
            cycle = on_path[on_path.index(concept_id) :] + [concept_id]
            raise GraphError("prerequisite cycle: " + " -> ".join(cycle))

        if concept_id not in done:
            on_path.append(concept_id)

            for prereq in graph[concept_id].prerequisites:
                visit(prereq)

            on_path.pop()
            done.add(concept_id)

    for concept_id in graph:
        visit(concept_id)
