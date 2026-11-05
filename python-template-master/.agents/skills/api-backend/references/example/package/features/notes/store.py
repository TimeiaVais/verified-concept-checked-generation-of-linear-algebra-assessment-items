"""The only code that writes the `note` table. Other features call these functions."""

import datetime
import uuid

import psycopg

from python_template.features.notes import schemas

__all__ = ["insert_note", "list_notes"]


def insert_note(connection: psycopg.Connection, body: str) -> schemas.Note:
    """Insert a note on `connection` and return it. The caller commits."""
    note_id = uuid.uuid4().hex
    created_at = datetime.datetime.now(datetime.timezone.utc)

    connection.execute(
        "INSERT INTO note (id, body, created_at) VALUES (%s, %s, %s)",
        (note_id, body, created_at),
    )
    note = schemas.Note(id=note_id, body=body, created_at=created_at)

    return note


def list_notes(connection: psycopg.Connection) -> list[schemas.Note]:
    """Return every note, oldest first."""
    rows = connection.execute("SELECT id, body, created_at FROM note ORDER BY created_at, id")
    notes = [schemas.Note(id=row[0], body=row[1], created_at=row[2]) for row in rows]

    return notes
