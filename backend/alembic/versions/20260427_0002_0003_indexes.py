"""add FK indexes and audit_log stub

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-27 13:30:00

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # FK indexes —ускоряют JOIN-ы по внешним ключам
    op.execute("CREATE INDEX IF NOT EXISTS ix_rentals_equipment_id ON rentals(equipment_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_rentals_status ON rentals(status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_inspections_equipment_id ON inspections(equipment_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_inspections_rental_id ON inspections(rental_id) WHERE rental_id IS NOT NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_kanban_cards_equipment_id ON kanban_cards(equipment_id)")
    op.execute('CREATE INDEX IF NOT EXISTS ix_kanban_cards_column ON kanban_cards("column")')

    # Audit log — кто что когда делал
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id BIGSERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            action VARCHAR(64) NOT NULL,
            entity_type VARCHAR(64),
            entity_id INTEGER,
            detail TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_log_entity ON audit_log(entity_type, entity_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_log_created ON audit_log(created_at DESC)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS audit_log")
    op.execute("DROP INDEX IF EXISTS ix_rentals_equipment_id")
    op.execute("DROP INDEX IF EXISTS ix_rentals_status")
    op.execute("DROP INDEX IF EXISTS ix_inspections_equipment_id")
    op.execute("DROP INDEX IF EXISTS ix_inspections_rental_id")
    op.execute("DROP INDEX IF EXISTS ix_kanban_cards_equipment_id")
    op.execute("DROP INDEX IF EXISTS ix_kanban_cards_column")
