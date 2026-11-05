"""The notes feature's models. A request body ends in `Request`, a response in `Response`."""

import datetime

import pydantic

__all__ = ["CreateNoteRequest", "Note", "NoteResponse"]


class Note(pydantic.BaseModel):
    """A note, as the store holds it."""

    id: str
    body: str
    created_at: datetime.datetime


class NoteResponse(Note):
    """The model is also used inside, so the API gets a subclass named for its direction."""

    __doc__ = Note.__doc__


class CreateNoteRequest(pydantic.BaseModel):
    """The body of `POST /notes`."""

    body: str = pydantic.Field(min_length=1)
