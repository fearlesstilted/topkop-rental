from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Equipment, EquipmentCategory, Rental
from app.models.enums import EquipmentStatus, RentalStatus
from app.schemas.rental import RentalCreate, RentalUpdate


@dataclass(frozen=True)
class ClientHistoryRow:
    name: str
    nip: str
    address: str
    phone: str


@dataclass(frozen=True)
class DashboardSummary:
    active_rentals: int
    equipment_out: int
    ending_today: list[Rental]
    ending_week: int
    month_revenue: Decimal


class RentalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_rentals(self) -> list[Rental]:
        result = await self._session.execute(select(Rental).order_by(Rental.created_at.desc()))
        return list(result.scalars())

    async def get_rental(self, rental_id: int) -> Rental | None:
        return await self._session.get(Rental, rental_id)

    async def create_rental(
        self,
        payload: RentalCreate,
        *,
        rental_days: int,
        subtotal: Decimal,
        total_netto: Decimal,
    ) -> Rental:
        rental = Rental(
            equipment_id=payload.equipment_id,
            client_name=payload.client_name,
            client_nip=payload.client_nip,
            client_address=payload.client_address,
            client_phone=payload.client_phone,
            start_date=payload.start_date,
            end_date=payload.end_date,
            weekdays_only=payload.weekdays_only,
            align_to_monday=payload.align_to_monday,
            rate_tier_1_7=payload.rate_tier_1_7,
            rate_above_7=payload.rate_above_7,
            flat_rate=payload.flat_rate,
            daily_limit=payload.daily_limit,
            overage_rate=payload.overage_rate,
            discount_pct=payload.discount_pct,
            surcharge_pct=payload.surcharge_pct,
            rental_days=rental_days,
            subtotal=subtotal,
            total_netto=total_netto,
            billing_entity=payload.billing_entity,
            notes=payload.notes,
        )
        self._session.add(rental)
        await self._session.commit()
        await self._session.refresh(rental)
        return rental

    async def update_rental_fields(
        self,
        rental: Rental,
        payload: RentalUpdate,
    ) -> set[str]:
        updated = payload.model_dump(exclude_unset=True)
        for key, value in updated.items():
            setattr(rental, key, value)
        return set(updated)

    async def save_rental(self, rental: Rental) -> Rental:
        await self._session.commit()
        await self._session.refresh(rental)
        return rental

    async def delete_rental(self, rental: Rental) -> None:
        await self._session.delete(rental)
        await self._session.commit()

    async def get_latest_by_client_nip(self, nip: str) -> Rental | None:
        result = await self._session.execute(
            select(Rental)
            .where(Rental.client_nip == nip)
            .order_by(Rental.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_client_history(self, query: str, limit: int) -> list[ClientHistoryRow]:
        stmt = select(
            Rental.client_name,
            Rental.client_nip,
            Rental.client_address,
            Rental.client_phone,
        ).distinct(Rental.client_nip, Rental.client_name)

        if query:
            like = f"%{query}%"
            stmt = stmt.where(
                or_(Rental.client_name.ilike(like), Rental.client_nip.ilike(like))
            )

        rows = (await self._session.execute(stmt.order_by(Rental.client_name).limit(limit))).all()
        return [
            ClientHistoryRow(
                name=row.client_name,
                nip=row.client_nip or "",
                address=row.client_address or "",
                phone=row.client_phone or "",
            )
            for row in rows
        ]

    async def get_dashboard_summary(
        self,
        *,
        today: date,
        month_start: date,
        week_end: date,
    ) -> DashboardSummary:
        active_rentals = (
            await self._session.execute(
                select(func.count()).where(Rental.status == RentalStatus.ACTIVE)
            )
        ).scalar_one()
        equipment_out = (
            await self._session.execute(
                select(func.count()).where(Equipment.status == EquipmentStatus.RENTED)
            )
        ).scalar_one()
        ending_today = (
            await self._session.execute(
                select(Rental).where(
                    Rental.status == RentalStatus.ACTIVE,
                    Rental.end_date == today,
                )
            )
        ).scalars().all()
        ending_week = (
            await self._session.execute(
                select(func.count()).where(
                    Rental.status == RentalStatus.ACTIVE,
                    Rental.end_date > today,
                    Rental.end_date <= week_end,
                )
            )
        ).scalar_one()
        month_revenue = (
            await self._session.execute(
                select(func.coalesce(func.sum(Rental.total_netto), 0)).where(
                    Rental.status.in_([RentalStatus.ACTIVE, RentalStatus.RETURNED]),
                    Rental.start_date >= month_start,
                )
            )
        ).scalar_one()
        return DashboardSummary(
            active_rentals=active_rentals,
            equipment_out=equipment_out,
            ending_today=list(ending_today),
            ending_week=ending_week,
            month_revenue=month_revenue,
        )

    async def get_equipment(self, equipment_id: int) -> Equipment | None:
        return await self._session.get(Equipment, equipment_id)

    async def get_category(self, category_id: int) -> EquipmentCategory | None:
        return await self._session.get(EquipmentCategory, category_id)
