"""Imports every feature's `tables.py`, so `db_metadata.metadata` holds all the declared tables.

Alembic's `env.py` and the metadata test import this module and nothing else.
"""

from python_template.features.notes import tables as notes_tables

__all__ = ["notes_tables"]
