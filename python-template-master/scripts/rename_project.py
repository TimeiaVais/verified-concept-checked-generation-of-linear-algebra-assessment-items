"""Rename the template's placeholder project to a real name.

Usage: python3 scripts/rename_project.py my-project-name

It replaces `python-template` and `python_template` in every text file, renames
`src/python_template`, and deletes itself and its test, which only make sense in the template.
It does not touch `.git`. Check the result by hand afterwards (the script prints what to look at).
"""

import argparse
import keyword
import os
import pathlib
import re
import sys
import typing

PLACEHOLDER_PROJECT_NAME: typing.Final = "python-template"
PLACEHOLDER_PACKAGE_NAME: typing.Final = "python_template"
SKIPPED_FOLDER_NAMES: typing.Final = frozenset(
    {
        ".git",
        ".idea",
        ".venv",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "build",
        "dist",
        "htmlcov",
    }
)
TEMPLATE_ONLY_FILES: typing.Final = ("scripts/rename_project.py", "tests/test_rename_project.py")


def derive_package_name(project_name: str) -> str:
    """Return the import name for a project name: `my-project` gives `my_project`.

    Parameters
    ----------
    project_name : str
        Lowercase words joined by hyphens.

    Returns
    -------
    package_name : str
        The name to import the package by.

    Raises
    ------
    ValueError
        If the name is malformed, is the placeholder, or would shadow a keyword or a standard
        library module.
    """
    package_name = project_name.replace("-", "_")

    if re.fullmatch(r"[a-z][a-z0-9]*(-[a-z0-9]+)*", project_name) is None:
        raise ValueError(f"{project_name!r} must be lowercase words joined by hyphens")
    if project_name == PLACEHOLDER_PROJECT_NAME:
        raise ValueError(f"{project_name!r} is the placeholder, pick the real name")
    if keyword.iskeyword(package_name) or package_name in sys.stdlib_module_names:
        raise ValueError(f"{package_name!r} would shadow a keyword or a standard library module")

    return package_name


def list_project_files(root: pathlib.Path) -> list[pathlib.Path]:
    """Return every file under `root` except symlinks and the folders in `SKIPPED_FOLDER_NAMES`."""
    project_files = []

    for folder, folder_names, file_names in os.walk(root):
        folder_names[:] = [name for name in folder_names if name not in SKIPPED_FOLDER_NAMES]

        for file_name in file_names:
            path = pathlib.Path(folder) / file_name
            if not path.is_symlink():
                project_files.append(path)

    return project_files


def replace_placeholders(path: pathlib.Path, project_name: str, package_name: str) -> bool:
    """Replace both placeholder names in a text file. Return whether the file changed.

    A file that is not UTF-8 text is left as it is.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = None

    is_changed = False
    if text is not None:
        new_text = text.replace(PLACEHOLDER_PROJECT_NAME, project_name).replace(
            PLACEHOLDER_PACKAGE_NAME, package_name
        )
        is_changed = new_text != text
        if is_changed:
            path.write_text(new_text, encoding="utf-8")

    return is_changed


def rename_project(root: pathlib.Path, project_name: str) -> list[pathlib.Path]:
    """Rename the placeholder project under `root`. Return the files whose text changed.

    Raises
    ------
    ValueError
        If the project name is not acceptable (see `derive_package_name`).
    FileNotFoundError
        If `src/python_template` is missing, for example because the project was renamed already.
    """
    package_name = derive_package_name(project_name)
    package_folder = root / "src" / PLACEHOLDER_PACKAGE_NAME
    template_only_paths = [root / relative_path for relative_path in TEMPLATE_ONLY_FILES]

    if not package_folder.is_dir():
        raise FileNotFoundError(f"{package_folder} not found: was the project renamed already?")

    changed_files = [
        path
        for path in list_project_files(root)
        if path not in template_only_paths
        and replace_placeholders(path, project_name, package_name)
    ]
    package_folder.rename(root / "src" / package_name)

    for path in template_only_paths:
        path.unlink(missing_ok=True)

    scripts_folder = root / "scripts"
    if scripts_folder.is_dir() and not any(scripts_folder.iterdir()):
        scripts_folder.rmdir()

    return changed_files


def main() -> None:
    """Rename the project in the repository this script lives in."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("project_name", help="lowercase words joined by hyphens, e.g. my-project")
    arguments = parser.parse_args()

    root = pathlib.Path(__file__).resolve().parent.parent
    changed_files = rename_project(root, arguments.project_name)

    for path in changed_files:
        print(f"updated {path.relative_to(root)}")
    print(f"renamed src/{PLACEHOLDER_PACKAGE_NAME}; removed the rename script and its test")
    print("Check by hand: README.md (it describes the template), the description in")
    print("pyproject.toml, docs/glossary.md, and `git diff`. Then run `make bootstrap`.")


if __name__ == "__main__":
    main()
