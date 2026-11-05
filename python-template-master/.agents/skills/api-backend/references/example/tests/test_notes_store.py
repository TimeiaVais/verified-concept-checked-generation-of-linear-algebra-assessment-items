import psycopg
import pytest

from python_template.features.notes import store
from python_template.infra import db


def test_inserted_notes_are_listed_oldest_first(empty_database: str) -> None:
    with db.open_connection() as connection:
        first = store.insert_note(connection, "first")
        second = store.insert_note(connection, "second")

    with db.open_connection() as connection:
        notes = store.list_notes(connection)

    assert [note.id for note in notes] == [first.id, second.id]


def test_the_database_refuses_an_empty_note(empty_database: str) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        with db.open_connection() as connection:
            store.insert_note(connection, "")
