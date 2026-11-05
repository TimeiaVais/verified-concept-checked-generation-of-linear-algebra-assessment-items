"""Create the note table.

Revision ID: 0001
Revises:
Create Date: 2026-10-28
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE note (
            id          TEXT PRIMARY KEY,
            body        TEXT NOT NULL,
            created_at  TIMESTAMPTZ NOT NULL,
            CONSTRAINT note_body_check CHECK (body <> ''::text)
        );

        COMMENT ON TABLE note IS 'A note a user wrote. Owned by the notes feature.';
    """)


def downgrade() -> None:
    op.execute("DROP TABLE note")
