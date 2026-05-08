"""add billing_entity to rentals

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-27 12:50:00

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE billing_entity AS ENUM ('topkop_jdg', 'tk_spzoo');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        ALTER TABLE rentals
        ADD COLUMN IF NOT EXISTS billing_entity billing_entity NOT NULL DEFAULT 'topkop_jdg'
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE rentals DROP COLUMN IF EXISTS billing_entity")
    op.execute("DROP TYPE IF EXISTS billing_entity")
