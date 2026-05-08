from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Equipment, EquipmentCategory, Rental
from app.models.enums import EquipmentStatus, RentalStatus, TrackingType
from app.schemas.equipment import (
    CategoryCreate,
    CategoryUpdate,
    EquipmentCreate,
    EquipmentUpdate,
)


class EquipmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_categories(self) -> list[EquipmentCategory]:
        result = await self._session.execute(
            select(EquipmentCategory).order_by(
                EquipmentCategory.sort_order,
                EquipmentCategory.name_pl,
            )
        )
        return list(result.scalars())

    async def list_category_slugs(self) -> set[str]:
        result = await self._session.execute(select(EquipmentCategory.slug))
        return set(result.scalars())

    async def get_category(self, category_id: int) -> EquipmentCategory | None:
        return await self._session.get(EquipmentCategory, category_id)

    async def get_category_by_slug(self, slug: str) -> EquipmentCategory | None:
        result = await self._session.execute(
            select(EquipmentCategory).where(EquipmentCategory.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create_category(self, payload: CategoryCreate) -> EquipmentCategory:
        category = EquipmentCategory(**payload.model_dump())
        self._session.add(category)
        await self._session.commit()
        await self._session.refresh(category)
        return category

    async def add_category(
        self,
        *,
        slug: str,
        name_pl: str,
        default_tracking: TrackingType,
        sort_order: int,
    ) -> EquipmentCategory:
        category = EquipmentCategory(
            slug=slug,
            name_pl=name_pl,
            default_tracking=default_tracking,
            sort_order=sort_order,
        )
        self._session.add(category)
        await self._session.flush()
        return category

    async def update_category(
        self,
        category: EquipmentCategory,
        payload: CategoryUpdate,
    ) -> EquipmentCategory:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(category, key, value)
        await self._session.commit()
        await self._session.refresh(category)
        return category

    async def list_equipment(self, category_id: int | None = None) -> list[Equipment]:
        stmt = select(Equipment).order_by(Equipment.code)
        if category_id is not None:
            stmt = stmt.where(Equipment.category_id == category_id)
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def get_equipment(self, equipment_id: int) -> Equipment | None:
        return await self._session.get(Equipment, equipment_id)

    async def get_equipment_by_code(self, code: str) -> Equipment | None:
        result = await self._session.execute(select(Equipment).where(Equipment.code == code))
        return result.scalar_one_or_none()

    async def create_equipment(self, payload: EquipmentCreate) -> Equipment:
        equipment = Equipment(**payload.model_dump())
        self._session.add(equipment)
        await self._session.commit()
        await self._session.refresh(equipment)
        return equipment

    async def add_equipment(
        self,
        *,
        category_id: int,
        code: str,
        name: str,
        manufacturer: str | None,
        model: str | None,
        tracking_type: TrackingType,
        rate_tier_1_7: Decimal,
        rate_above_7: Decimal,
        daily_limit: int | None,
        overage_rate: Decimal | None,
        status: EquipmentStatus,
    ) -> Equipment:
        equipment = Equipment(
            category_id=category_id,
            code=code,
            name=name,
            manufacturer=manufacturer,
            model=model,
            tracking_type=tracking_type,
            rate_tier_1_7=rate_tier_1_7,
            rate_above_7=rate_above_7,
            daily_limit=daily_limit,
            overage_rate=overage_rate,
            status=status,
        )
        self._session.add(equipment)
        await self._session.flush()
        return equipment

    async def update_equipment(
        self,
        equipment: Equipment,
        payload: EquipmentUpdate,
    ) -> Equipment:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(equipment, key, value)
        await self._session.commit()
        await self._session.refresh(equipment)
        return equipment

    async def has_active_rental(self, equipment_id: int) -> bool:
        result = await self._session.execute(
            select(Rental.id).where(
                Rental.equipment_id == equipment_id,
                Rental.status == RentalStatus.ACTIVE,
            )
        )
        return result.scalar_one_or_none() is not None

    async def delete_equipment(self, equipment: Equipment) -> None:
        await self._session.delete(equipment)
        await self._session.commit()

    async def commit(self) -> None:
        await self._session.commit()
