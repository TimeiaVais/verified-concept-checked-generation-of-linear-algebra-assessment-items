from pathlib import Path

import pytest

from graph.loader import GraphError, load_graph


def write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "g.yaml"
    path.write_text("concepts:\n" + body, encoding="utf-8")
    return path


def concept(cid: str, prereqs: str = "[]", block: str = "matrices") -> str:
    return (
        f"  - id: {cid}\n    name_uk: x\n    name_en: x\n"
        f"    block: {block}\n    prerequisites: {prereqs}\n    source: x\n"
    )


def test_real_graph_loads() -> None:
    graph = load_graph()
    assert 20 <= len(graph) <= 30
    assert all(c.source for c in graph.values())


def test_duplicate_id(tmp_path: Path) -> None:
    with pytest.raises(GraphError, match="duplicate"):
        load_graph(write(tmp_path, concept("a") + concept("a")))


def test_unknown_block(tmp_path: Path) -> None:
    with pytest.raises(GraphError, match="unknown block"):
        load_graph(write(tmp_path, concept("a", block="geometry")))


def test_unknown_prerequisite(tmp_path: Path) -> None:
    with pytest.raises(GraphError, match="unknown prerequisite"):
        load_graph(write(tmp_path, concept("a", "[b]")))


def test_self_prerequisite(tmp_path: Path) -> None:
    with pytest.raises(GraphError, match="own prerequisite"):
        load_graph(write(tmp_path, concept("a", "[a]")))


def test_cycle(tmp_path: Path) -> None:
    body = concept("a", "[c]") + concept("b", "[a]") + concept("c", "[b]")
    with pytest.raises(GraphError, match="cycle"):
        load_graph(write(tmp_path, body))
