"""add estimated rental term fields

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-26 12:00:00

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE rentals
        ADD COLUMN IF NOT EXISTS is_term_estimated BOOLEAN NOT NULL DEFAULT FALSE
    """)
    op.execute("""
        ALTER TABLE rentals
        ADD COLUMN IF NOT EXISTS term_note VARCHAR(300)
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE rentals DROP COLUMN IF EXISTS term_note")
    op.execute("ALTER TABLE rentals DROP COLUMN IF EXISTS is_term_estimated")
