from pathlib import Path

import pytest

from la_items.graph import loader


def write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "g.yaml"
    path.write_text("concepts:\n" + body, encoding="utf-8")
    return path


def concept(concept_id: str, prereqs: str = "[]", block: str = "matrices") -> str:
    return (
        f"  - id: {concept_id}\n    name_uk: x\n    name_en: x\n"
        f"    block: {block}\n    prerequisites: {prereqs}\n    source: x\n"
    )


def test_real_graph_loads() -> None:
    graph = loader.load_graph()
    assert 20 <= len(graph) <= 30
    assert all(c.source for c in graph.values())


def test_duplicate_id(tmp_path: Path) -> None:
    with pytest.raises(loader.GraphError, match="duplicate"):
        loader.load_graph(write(tmp_path, concept("a") + concept("a")))


def test_unknown_block(tmp_path: Path) -> None:
    with pytest.raises(loader.GraphError, match="unknown block"):
        loader.load_graph(write(tmp_path, concept("a", block="geometry")))


def test_unknown_prerequisite(tmp_path: Path) -> None:
    with pytest.raises(loader.GraphError, match="unknown prerequisite"):
        loader.load_graph(write(tmp_path, concept("a", "[b]")))


def test_self_prerequisite(tmp_path: Path) -> None:
    with pytest.raises(loader.GraphError, match="own prerequisite"):
        loader.load_graph(write(tmp_path, concept("a", "[a]")))


def test_cycle(tmp_path: Path) -> None:
    body = concept("a", "[c]") + concept("b", "[a]") + concept("c", "[b]")
    with pytest.raises(loader.GraphError, match="cycle"):
        loader.load_graph(write(tmp_path, body))
