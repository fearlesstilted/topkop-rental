"""add manual rental total fields

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-27 12:00:00

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE rentals
        ADD COLUMN IF NOT EXISTS manual_total_enabled BOOLEAN NOT NULL DEFAULT FALSE
    """)
    op.execute("""
        ALTER TABLE rentals
        ADD COLUMN IF NOT EXISTS manual_total_netto NUMERIC(12,2)
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE rentals DROP COLUMN IF EXISTS manual_total_netto")
    op.execute("ALTER TABLE rentals DROP COLUMN IF EXISTS manual_total_enabled")
