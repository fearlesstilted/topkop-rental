from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Equipment, KanbanCard, KanbanChecklistItem
from app.schemas.kanban import CardCreate, CardUpdate


class KanbanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_cards(self) -> list[KanbanCard]:
        result = await self._session.execute(
            select(KanbanCard)
            .options(selectinload(KanbanCard.checklist))
            .order_by(KanbanCard.sort_order, KanbanCard.id)
        )
        return list(result.scalars())

    async def get_card_with_checklist(self, card_id: int) -> KanbanCard | None:
        result = await self._session.execute(
            select(KanbanCard)
            .options(selectinload(KanbanCard.checklist))
            .where(KanbanCard.id == card_id)
        )
        return result.scalar_one_or_none()

    async def get_equipment(self, equipment_id: int) -> Equipment | None:
        return await self._session.get(Equipment, equipment_id)

    async def create_card(self, payload: CardCreate) -> KanbanCard:
        card = KanbanCard(
            equipment_id=payload.equipment_id,
            rental_id=payload.rental_id,
            title=payload.title,
            notes=payload.notes,
        )
        for idx, item in enumerate(payload.checklist):
            card.checklist.append(
                KanbanChecklistItem(label=item.label, sort_order=item.sort_order or idx)
            )
        self._session.add(card)
        await self._session.commit()
        refreshed = await self.get_card_with_checklist(card.id)
        if refreshed is None:
            raise RuntimeError("Kanban card was not persisted")
        return refreshed

    async def apply_card_update(
        self,
        card: KanbanCard,
        payload: CardUpdate,
    ) -> set[str]:
        data = payload.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(card, key, value)
        return set(data)

    async def get_checklist_item(self, item_id: int) -> KanbanChecklistItem | None:
        return await self._session.get(KanbanChecklistItem, item_id)

    async def save_card(self, card: KanbanCard) -> KanbanCard:
        await self._session.commit()
        refreshed = await self.get_card_with_checklist(card.id)
        if refreshed is None:
            raise RuntimeError("Kanban card disappeared after save")
        return refreshed

    async def delete_card(self, card: KanbanCard) -> None:
        await self._session.delete(card)
        await self._session.commit()
