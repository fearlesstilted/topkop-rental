"""add operational fields to kanban cards

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-11 09:30:00

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE kanban_cards
        ADD COLUMN IF NOT EXISTS priority VARCHAR(16) NOT NULL DEFAULT 'normal'
    """)
    op.execute("""
        ALTER TABLE kanban_cards
        ADD COLUMN IF NOT EXISTS due_date DATE
    """)
    op.execute("""
        ALTER TABLE kanban_cards
        ADD COLUMN IF NOT EXISTS source VARCHAR(32) NOT NULL DEFAULT 'manual'
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE kanban_cards DROP COLUMN IF EXISTS source")
    op.execute("ALTER TABLE kanban_cards DROP COLUMN IF EXISTS due_date")
    op.execute("ALTER TABLE kanban_cards DROP COLUMN IF EXISTS priority")
