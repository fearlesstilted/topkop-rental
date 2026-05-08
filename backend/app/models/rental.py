from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import BillingEntity, RentalStatus

if TYPE_CHECKING:
    from app.models.equipment import Equipment
    from app.models.inspection import Inspection


class Rental(Base):
    """
    Snapshot-модель: rate_*, limit, overage копируются в момент создания
    чтобы изменение прайса у Equipment не ломало исторические контракты.
    """

    __tablename__ = "rentals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"), nullable=False)

    client_name: Mapped[str] = mapped_column(String(200), nullable=False)
    client_nip: Mapped[str | None] = mapped_column(String(32), nullable=True)
    client_address: Mapped[str | None] = mapped_column(String(400), nullable=True)
    client_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    weekdays_only: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    align_to_monday: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    rate_tier_1_7: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    rate_above_7: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    flat_rate: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True = не применять tier, всегда rate_tier_1_7",
    )
    daily_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    overage_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    discount_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0"), nullable=False
    )
    surcharge_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0"), nullable=False
    )

    rental_days: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_netto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    status: Mapped[RentalStatus] = mapped_column(
        SAEnum(
            RentalStatus,
            name="rental_status",
            values_callable=lambda o: [e.value for e in o],
        ),
        default=RentalStatus.DRAFT,
        nullable=False,
    )
    billing_entity: Mapped[BillingEntity] = mapped_column(
        SAEnum(
            BillingEntity,
            name="billing_entity",
            values_callable=lambda o: [e.value for e in o],
        ),
        default=BillingEntity.TOPKOP_JDG,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(String(400), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    equipment: Mapped[Equipment] = relationship(back_populates="rentals")
    inspections: Mapped[list[Inspection]] = relationship(back_populates="rental")
