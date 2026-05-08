"""add assigned_worker to kanban_cards

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-27 14:00:00

"""
from typing import Sequence, Union
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE kanban_cards
        ADD COLUMN IF NOT EXISTS assigned_worker VARCHAR(100)
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE kanban_cards DROP COLUMN IF EXISTS assigned_worker")
