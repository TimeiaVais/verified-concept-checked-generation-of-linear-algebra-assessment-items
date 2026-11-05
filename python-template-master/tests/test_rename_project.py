import importlib.util
import pathlib

import pytest

SCRIPT_PATH = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "rename_project.py"
SPEC = importlib.util.spec_from_file_location("rename_project", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
rename_project = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rename_project)


def write_file(path: pathlib.Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


def test_rename_replaces_both_names_and_moves_the_package(tmp_path: pathlib.Path) -> None:
    write_file(tmp_path / "pyproject.toml", 'name = "python-template"\nfrom = "src"\n')
    write_file(tmp_path / "src/python_template/__init__.py", "import python_template\n")
    write_file(tmp_path / "docs/notes.md", "no placeholder here\n")
    write_file(tmp_path / ".git/config", "python-template\n")
    write_file(tmp_path / "data.bin", b"\xff\xfepython-template")
    write_file(tmp_path / "scripts/rename_project.py", "python-template\n")
    write_file(tmp_path / "tests/test_rename_project.py", "python-template\n")

    changed_files = rename_project.rename_project(tmp_path, "my-demo")

    assert (tmp_path / "pyproject.toml").read_text() == 'name = "my-demo"\nfrom = "src"\n'
    assert (tmp_path / "src/my_demo/__init__.py").read_text() == "import my_demo\n"
    assert not (tmp_path / "src/python_template").exists()
    assert sorted(path.name for path in changed_files) == ["__init__.py", "pyproject.toml"]
    assert (tmp_path / ".git/config").read_text() == "python-template\n"
    assert (tmp_path / "data.bin").read_bytes() == b"\xff\xfepython-template"
    assert not (tmp_path / "scripts").exists()
    assert not (tmp_path / "tests/test_rename_project.py").exists()


@pytest.mark.parametrize("project_name", ["My_Project", "python-template", "os", "class", "-x", ""])
def test_rename_rejects_an_unacceptable_name(tmp_path: pathlib.Path, project_name: str) -> None:
    write_file(tmp_path / "src/python_template/__init__.py", "")

    with pytest.raises(ValueError):
        rename_project.rename_project(tmp_path, project_name)

    assert (tmp_path / "src/python_template").is_dir()
