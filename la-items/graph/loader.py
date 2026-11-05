"""Load the concept graph and check its integrity."""

from dataclasses import dataclass
from pathlib import Path

import yaml

GRAPH_PATH = Path(__file__).with_name("concepts.yaml")
BLOCKS = {"linear_systems", "matrices", "determinants", "eigenvalues"}


class GraphError(ValueError):
    pass


@dataclass(frozen=True)
class Concept:
    id: str
    name_uk: str
    name_en: str
    block: str
    prerequisites: tuple[str, ...]
    source: str


def load_graph(path: Path = GRAPH_PATH) -> dict[str, Concept]:
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

    def visit(cid: str) -> None:
        if cid in done:
            return
        if cid in on_path:
            cycle = on_path[on_path.index(cid):] + [cid]
            raise GraphError("prerequisite cycle: " + " -> ".join(cycle))
        on_path.append(cid)
        for prereq in graph[cid].prerequisites:
            visit(prereq)
        on_path.pop()
        done.add(cid)

    for cid in graph:
        visit(cid)
