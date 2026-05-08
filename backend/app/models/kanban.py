from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import KanbanColumn


class KanbanCard(Base):
    __tablename__ = "kanban_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id"), nullable=False)
    rental_id: Mapped[int | None] = mapped_column(ForeignKey("rentals.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    column: Mapped[KanbanColumn] = mapped_column(
        SAEnum(KanbanColumn, name="kanban_column", values_callable=lambda o: [e.value for e in o]),
        default=KanbanColumn.NA_SERWIS,
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assigned_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    assigned_worker: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    checklist: Mapped[list["KanbanChecklistItem"]] = relationship(
        back_populates="card",
        cascade="all, delete-orphan",
        order_by="KanbanChecklistItem.sort_order",
    )


class KanbanChecklistItem(Base):
    __tablename__ = "kanban_checklist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_id: Mapped[int] = mapped_column(
        ForeignKey("kanban_cards.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    done_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    card: Mapped[KanbanCard] = relationship(back_populates="checklist")
