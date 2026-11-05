"""The tables the notes feature owns, declared for Alembic autogenerate."""

import sqlalchemy

from python_template import db_metadata

__all__ = ["table_note"]

table_note = sqlalchemy.Table(
    "note",
    db_metadata.metadata,
    sqlalchemy.Column("id", sqlalchemy.Text, primary_key=True),
    sqlalchemy.Column("body", sqlalchemy.Text, nullable=False),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime(timezone=True), nullable=False),
    # Written the way Postgres reports it: the test compares name and text.
    sqlalchemy.CheckConstraint("body <> ''::text", name="body"),
    # The same text as `COMMENT ON TABLE` in the migration: autogenerate compares table comments.
    comment="A note a user wrote. Owned by the notes feature.",
)
