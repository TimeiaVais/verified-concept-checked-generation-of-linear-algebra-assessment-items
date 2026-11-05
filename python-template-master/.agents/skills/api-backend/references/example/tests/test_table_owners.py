"""Only the feature that declares a table writes to it.

The owner of a table is the feature whose `tables.py` declares it. A write is an `INSERT INTO`,
`UPDATE` or `DELETE FROM` in a string of a feature's code. A write the scan cannot resolve to a
table, such as `INSERT INTO {table_name}`, fails too: it cannot be checked.

shortcut: only `features/` is scanned and only string constants are read. Add `scripts/` when a
script writes a table, and move a table name that is built at run time into a constant.
"""

import ast
import importlib
import pathlib
import re

import pytest
import sqlalchemy

from python_template import features

FEATURES_FOLDER = pathlib.Path(features.__file__).resolve().parent
_WRITE = re.compile(r"\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+(\S+)", re.IGNORECASE)

# (feature, table) -> why that feature may write a table it does not own.
EXCEPTIONS: dict[tuple[str, str], str] = {}


def find_written_tables(source: str) -> set[str]:
    """Return the table token that follows each write statement in the strings of `source`.

    A piece of an f-string that is not text (`{table_name}`) reads as `{}`.
    """
    tokens = set()

    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value
        elif isinstance(node, ast.JoinedStr):
            text = "".join(
                part.value if isinstance(part, ast.Constant) else "{}" for part in node.values
            )
        else:
            continue

        tokens.update(match.group(1) for match in _WRITE.finditer(text))

    return tokens


def resolve_table_name(token: str) -> str | None:
    """Return the table name in a token such as `note`, `public.note` or `note(id,`, if any."""
    match = re.fullmatch(r'(?:\w+\.)?"?([A-Za-z_]\w*)"?\W*', token)
    table_name = match.group(1) if match else None

    return table_name


def list_feature_names() -> list[str]:
    feature_names = sorted(
        folder.name for folder in FEATURES_FOLDER.iterdir() if (folder / "tables.py").is_file()
    )

    return feature_names


def map_tables_to_owners() -> dict[str, str]:
    owners: dict[str, str] = {}

    for feature in list_feature_names():
        module = importlib.import_module(f"{features.__name__}.{feature}.tables")
        for value in vars(module).values():
            if isinstance(value, sqlalchemy.Table):
                assert value.name not in owners, f"{value.name} is declared twice"
                owners[value.name] = feature

    return owners


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ('c.execute("INSERT INTO note (id) VALUES (1)")', {"note"}),
        ('c.execute("update public.note set body = 1")', {"public.note"}),
        ('c.execute(f"DELETE FROM {table_name} WHERE 1")', {"{}"}),
        ('c.execute("SELECT * FROM note")', set()),
    ],
)
def test_the_scan_finds_writes(source: str, expected: set[str]) -> None:
    assert find_written_tables(source) == expected


def test_only_the_owning_feature_writes_a_table() -> None:
    owners = map_tables_to_owners()
    problems = []

    for feature in list_feature_names():
        for path in sorted((FEATURES_FOLDER / feature).rglob("*.py")):
            for token in sorted(find_written_tables(path.read_text(encoding="utf-8"))):
                table_name = resolve_table_name(token)
                where = f"{path.relative_to(FEATURES_FOLDER)}: {token!r}"

                if table_name is None:
                    problems.append(f"{where} is not a table name the scan can resolve")
                elif table_name not in owners:
                    problems.append(f"{where} writes a table no feature declares")
                elif owners[table_name] != feature and (feature, table_name) not in EXCEPTIONS:
                    problems.append(f"{where} writes a table owned by {owners[table_name]!r}")

    assert problems == []
