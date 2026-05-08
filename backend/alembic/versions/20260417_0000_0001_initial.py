"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-17 00:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_enum(name: str, values: list[str]) -> None:
    vals = ", ".join(f"'{v}'" for v in values)
    op.execute(f"""
        DO $$ BEGIN
            CREATE TYPE {name} AS ENUM ({vals});
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)


def upgrade() -> None:
    _create_enum("user_role", ["biuro", "mechanik", "manager"])
    _create_enum("tracking_type", ["mth", "rbh", "daily"])
    _create_enum("equipment_status", ["available", "rented", "service", "broken"])
    _create_enum("rental_status", ["draft", "active", "returned", "cancelled"])
    _create_enum("inspection_type", ["pickup", "return"])
    _create_enum("kanban_column", ["na_serwis", "w_trakcie", "gotowe", "wydana"])

    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            role user_role NOT NULL,
            pin_hash VARCHAR(255) NOT NULL,
            telegram_chat_id INTEGER,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS equipment_categories (
            id SERIAL PRIMARY KEY,
            slug VARCHAR(64) NOT NULL UNIQUE,
            name_pl VARCHAR(120) NOT NULL,
            default_tracking tracking_type NOT NULL DEFAULT 'daily',
            sort_order INTEGER NOT NULL DEFAULT 0
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            id SERIAL PRIMARY KEY,
            category_id INTEGER NOT NULL REFERENCES equipment_categories(id) ON DELETE RESTRICT,
            code VARCHAR(32) NOT NULL UNIQUE,
            name VARCHAR(150) NOT NULL,
            manufacturer VARCHAR(100),
            model VARCHAR(100),
            year INTEGER,
            tracking_type tracking_type NOT NULL DEFAULT 'daily',
            rate_tier_1_7 NUMERIC(10,2) NOT NULL,
            rate_above_7 NUMERIC(10,2) NOT NULL,
            daily_limit INTEGER,
            overage_rate NUMERIC(10,2),
            status equipment_status NOT NULL DEFAULT 'available',
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS rentals (
            id SERIAL PRIMARY KEY,
            equipment_id INTEGER NOT NULL REFERENCES equipment(id),
            client_name VARCHAR(200) NOT NULL,
            client_nip VARCHAR(32),
            client_address VARCHAR(400),
            client_phone VARCHAR(64),
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            weekdays_only BOOLEAN NOT NULL DEFAULT TRUE,
            align_to_monday BOOLEAN NOT NULL DEFAULT TRUE,
            rate_tier_1_7 NUMERIC(10,2) NOT NULL,
            rate_above_7 NUMERIC(10,2) NOT NULL,
            flat_rate BOOLEAN NOT NULL DEFAULT FALSE,
            daily_limit INTEGER,
            overage_rate NUMERIC(10,2),
            discount_pct NUMERIC(5,2) NOT NULL DEFAULT 0,
            surcharge_pct NUMERIC(5,2) NOT NULL DEFAULT 0,
            rental_days INTEGER NOT NULL,
            subtotal NUMERIC(12,2) NOT NULL,
            total_netto NUMERIC(12,2) NOT NULL,
            status rental_status NOT NULL DEFAULT 'draft',
            notes TEXT,
            pdf_path VARCHAR(400),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS inspections (
            id SERIAL PRIMARY KEY,
            rental_id INTEGER REFERENCES rentals(id),
            equipment_id INTEGER NOT NULL REFERENCES equipment(id),
            type inspection_type NOT NULL,
            meter_reading FLOAT,
            lat FLOAT,
            lon FLOAT,
            gps_accuracy_m FLOAT,
            signature_path VARCHAR(400),
            client_signer_name VARCHAR(200),
            notes TEXT,
            pdf_path VARCHAR(400),
            client_local_id VARCHAR(64) UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS inspection_photos (
            id SERIAL PRIMARY KEY,
            inspection_id INTEGER NOT NULL REFERENCES inspections(id) ON DELETE CASCADE,
            slot VARCHAR(32) NOT NULL,
            path VARCHAR(400) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS kanban_cards (
            id SERIAL PRIMARY KEY,
            equipment_id INTEGER NOT NULL REFERENCES equipment(id),
            rental_id INTEGER REFERENCES rentals(id),
            title VARCHAR(200) NOT NULL,
            "column" kanban_column NOT NULL DEFAULT 'na_serwis',
            sort_order INTEGER NOT NULL DEFAULT 0,
            assigned_user_id INTEGER REFERENCES users(id),
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS kanban_checklist_items (
            id SERIAL PRIMARY KEY,
            card_id INTEGER NOT NULL REFERENCES kanban_cards(id) ON DELETE CASCADE,
            label VARCHAR(200) NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE,
            sort_order INTEGER NOT NULL DEFAULT 0,
            done_at TIMESTAMPTZ,
            done_by_user_id INTEGER REFERENCES users(id)
        )
    """)


def downgrade() -> None:
    for table in [
        "kanban_checklist_items", "kanban_cards", "inspection_photos",
        "inspections", "rentals", "equipment", "equipment_categories", "users",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

    for name in ["kanban_column", "inspection_type", "rental_status",
                 "equipment_status", "tracking_type", "user_role"]:
        op.execute(f"DROP TYPE IF EXISTS {name}")
