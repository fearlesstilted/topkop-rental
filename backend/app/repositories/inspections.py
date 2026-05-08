from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Equipment, Inspection, InspectionPhoto
from app.schemas.inspection import InspectionCreate


class InspectionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_inspections(self) -> list[Inspection]:
        result = await self._session.execute(
            select(Inspection)
            .options(selectinload(Inspection.photos))
            .order_by(Inspection.created_at.desc())
        )
        return list(result.scalars())

    async def get_inspection_with_photos(self, inspection_id: int) -> Inspection | None:
        result = await self._session.execute(
            select(Inspection)
            .options(selectinload(Inspection.photos))
            .where(Inspection.id == inspection_id)
        )
        return result.scalar_one_or_none()

    async def get_by_client_local_id(self, client_local_id: str) -> Inspection | None:
        result = await self._session.execute(
            select(Inspection)
            .options(selectinload(Inspection.photos))
            .where(Inspection.client_local_id == client_local_id)
        )
        return result.scalar_one_or_none()

    async def get_equipment(self, equipment_id: int) -> Equipment | None:
        return await self._session.get(Equipment, equipment_id)

    async def get_equipment_map(self, equipment_ids: set[int]) -> dict[int, Equipment]:
        if not equipment_ids:
            return {}
        result = await self._session.execute(
            select(Equipment).where(Equipment.id.in_(equipment_ids))
        )
        return {equipment.id: equipment for equipment in result.scalars()}

    async def create_inspection(
        self,
        payload: InspectionCreate,
        *,
        signature_path: str | None,
        photos: list[tuple[str, str]],
    ) -> Inspection:
        inspection = Inspection(
            equipment_id=payload.equipment_id,
            rental_id=payload.rental_id,
            type=payload.type,
            meter_reading=payload.meter_reading,
            lat=payload.lat,
            lon=payload.lon,
            gps_accuracy_m=payload.gps_accuracy_m,
            signature_path=signature_path,
            client_signer_name=payload.client_signer_name,
            notes=payload.notes,
            client_local_id=payload.client_local_id,
        )
        self._session.add(inspection)
        await self._session.flush()

        for slot, path in photos:
            self._session.add(
                InspectionPhoto(inspection_id=inspection.id, slot=slot, path=path)
            )

        await self._session.commit()
        refreshed = await self.get_inspection_with_photos(inspection.id)
        if refreshed is None:
            raise RuntimeError("Inspection was not persisted")
        return refreshed
