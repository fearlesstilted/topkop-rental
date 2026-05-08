from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import EquipmentStatus, TrackingType

if TYPE_CHECKING:
    from app.models.inspection import Inspection
    from app.models.rental import Rental


class EquipmentCategory(Base):
    """18 категорий парка (koparki, ładowarki, walce, ...), расширяемо."""

    __tablename__ = "equipment_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name_pl: Mapped[str] = mapped_column(String(120), nullable=False)
    default_tracking: Mapped[TrackingType] = mapped_column(
        SAEnum(
            TrackingType,
            name="tracking_type",
            values_callable=lambda o: [e.value for e in o],
        ),
        default=TrackingType.DAILY_ONLY,
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    equipment: Mapped[list[Equipment]] = relationship(back_populates="category")


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("equipment_categories.id", ondelete="RESTRICT"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tracking_type: Mapped[TrackingType] = mapped_column(
        SAEnum(
            TrackingType,
            name="tracking_type",
            values_callable=lambda o: [e.value for e in o],
        ),
        default=TrackingType.DAILY_ONLY,
        nullable=False,
    )
    rate_tier_1_7: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    rate_above_7: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    daily_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    overage_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[EquipmentStatus] = mapped_column(
        SAEnum(
            EquipmentStatus,
            name="equipment_status",
            values_callable=lambda o: [e.value for e in o],
        ),
        default=EquipmentStatus.AVAILABLE,
        nullable=False,
    )
    registration_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    category: Mapped[EquipmentCategory] = relationship(back_populates="equipment")
    rentals: Mapped[list[Rental]] = relationship(back_populates="equipment")
    inspections: Mapped[list[Inspection]] = relationship(back_populates="equipment")
