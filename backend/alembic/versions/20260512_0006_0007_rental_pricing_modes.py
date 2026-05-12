"""add rental pricing modes and transport fields

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-12 13:45:00

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE rental_billing_mode AS ENUM ('daily', 'hourly');
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        ALTER TABLE rentals
        ADD COLUMN IF NOT EXISTS billing_mode rental_billing_mode NOT NULL DEFAULT 'daily'
    """)
    op.execute("""
        ALTER TABLE rentals
        ADD COLUMN IF NOT EXISTS operator_included BOOLEAN NOT NULL DEFAULT FALSE
    """)
    op.execute("""
        ALTER TABLE rentals
        ADD COLUMN IF NOT EXISTS operator_hours NUMERIC(8,2)
    """)
    op.execute("""
        ALTER TABLE rentals
        ADD COLUMN IF NOT EXISTS hourly_rate NUMERIC(10,2)
    """)
    op.execute("""
        ALTER TABLE rentals
        ADD COLUMN IF NOT EXISTS transport_cost NUMERIC(12,2) NOT NULL DEFAULT 0
    """)
    op.execute("""
        ALTER TABLE rentals
        ADD COLUMN IF NOT EXISTS transport_description VARCHAR(200)
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE rentals DROP COLUMN IF EXISTS transport_description")
    op.execute("ALTER TABLE rentals DROP COLUMN IF EXISTS transport_cost")
    op.execute("ALTER TABLE rentals DROP COLUMN IF EXISTS hourly_rate")
    op.execute("ALTER TABLE rentals DROP COLUMN IF EXISTS operator_hours")
    op.execute("ALTER TABLE rentals DROP COLUMN IF EXISTS operator_included")
    op.execute("ALTER TABLE rentals DROP COLUMN IF EXISTS billing_mode")
    op.execute("DROP TYPE IF EXISTS rental_billing_mode")
