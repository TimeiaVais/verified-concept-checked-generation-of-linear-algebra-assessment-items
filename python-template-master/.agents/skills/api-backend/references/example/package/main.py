"""The API application."""

import fastapi

from python_template.features.notes import router as notes_router

__all__ = ["app"]

app = fastapi.FastAPI(title="python-template")
app.include_router(notes_router.router)
