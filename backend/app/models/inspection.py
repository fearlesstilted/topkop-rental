from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import InspectionType

if TYPE_CHECKING:
    from app.models.equipment import Equipment
    from app.models.rental import Rental


class Inspection(Base):
    __tablename__ = "inspections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rental_id: Mapped[int | None] = mapped_column(ForeignKey("rentals.id"), nullable=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"), nullable=False)

    type: Mapped[InspectionType] = mapped_column(
        SAEnum(
            InspectionType,
            name="inspection_type",
            values_callable=lambda o: [e.value for e in o],
        ),
        nullable=False,
    )

    meter_reading: Mapped[float | None] = mapped_column(Float, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    gps_accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)

    signature_path: Mapped[str | None] = mapped_column(String(400), nullable=True)
    client_signer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(String(400), nullable=True)

    client_local_id: Mapped[str | None] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
        comment="UUID с клиента (Dexie) для idempotent offline sync",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    rental: Mapped[Rental | None] = relationship(back_populates="inspections")
    equipment: Mapped[Equipment] = relationship(back_populates="inspections")
    photos: Mapped[list[InspectionPhoto]] = relationship(
        back_populates="inspection", cascade="all, delete-orphan"
    )


class InspectionPhoto(Base):
    __tablename__ = "inspection_photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inspection_id: Mapped[int] = mapped_column(
        ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False
    )
    slot: Mapped[str] = mapped_column(String(32), nullable=False)
    path: Mapped[str] = mapped_column(String(400), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    inspection: Mapped[Inspection] = relationship(back_populates="photos")
