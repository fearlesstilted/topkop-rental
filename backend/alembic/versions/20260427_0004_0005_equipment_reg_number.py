"""add registration_number to equipment

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-27

"""
from typing import Sequence, Union
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE equipment ADD COLUMN IF NOT EXISTS registration_number VARCHAR(32)")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS telegram_chat_id")


def downgrade() -> None:
    op.execute("ALTER TABLE equipment DROP COLUMN IF EXISTS registration_number")
