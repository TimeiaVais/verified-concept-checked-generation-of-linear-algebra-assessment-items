"""The notes endpoints."""

import fastapi

from python_template.features.notes import schemas, store
from python_template.infra import db

__all__ = ["router"]

router = fastapi.APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=schemas.NoteResponse, status_code=201)
def create_note(request: schemas.CreateNoteRequest) -> schemas.Note:
    """Create a note."""
    with db.open_connection() as connection:
        note = store.insert_note(connection, request.body)

    return note


@router.get("", response_model=list[schemas.NoteResponse])
def list_notes() -> list[schemas.Note]:
    """List the notes, oldest first."""
    with db.open_connection() as connection:
        notes = store.list_notes(connection)

    return notes
