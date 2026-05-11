from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, require_roles
from app.database import get_session
from app.models import Equipment, KanbanCard, KanbanChecklistItem, Rental, User, UserRole
from app.models.enums import KanbanColumn
from app.schemas.kanban import CardCreate, CardOut, CardUpdate
from app.services.notification_service import notify_mechaniks_new_card
from app.services.ws_manager import broadcaster

router = APIRouter()


async def _serialize_cards(
    session: AsyncSession,
    cards: list[KanbanCard],
) -> list[CardOut]:
    equipment_ids = {card.equipment_id for card in cards}
    rental_ids = {card.rental_id for card in cards if card.rental_id is not None}

    equipment_map: dict[int, Equipment] = {}
    if equipment_ids:
        equipment_result = await session.execute(
            select(Equipment).where(Equipment.id.in_(equipment_ids))
        )
        equipment_map = {item.id: item for item in equipment_result.scalars()}

    rental_map: dict[int, Rental] = {}
    if rental_ids:
        rental_result = await session.execute(select(Rental).where(Rental.id.in_(rental_ids)))
        rental_map = {item.id: item for item in rental_result.scalars()}

    output: list[CardOut] = []
    for card in cards:
        equipment = equipment_map.get(card.equipment_id)
        rental = rental_map.get(card.rental_id) if card.rental_id is not None else None
        output.append(
            CardOut.model_validate(card).model_copy(
                update={
                    "equipment_code": equipment.code if equipment else None,
                    "equipment_name": equipment.name if equipment else None,
                    "rental_client_name": rental.client_name if rental else None,
                    "rental_status": rental.status.value if rental else None,
                }
            )
        )

    return output


async def _card_with_checklist(session: AsyncSession, card_id: int) -> KanbanCard:
    result = await session.execute(
        select(KanbanCard)
        .options(selectinload(KanbanCard.checklist))
        .where(KanbanCard.id == card_id)
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="Not found")
    return card


def _auto_advance_column(card: KanbanCard) -> bool:
    if not card.checklist:
        return False

    any_done = any(i.done for i in card.checklist)
    all_done = all(i.done for i in card.checklist)
    prev = card.column

    if all_done and card.column in (KanbanColumn.NA_SERWIS, KanbanColumn.W_TRAKCIE):
        card.column = KanbanColumn.GOTOWE
    elif any_done and card.column == KanbanColumn.NA_SERWIS:
        card.column = KanbanColumn.W_TRAKCIE
    elif not all_done and card.column == KanbanColumn.GOTOWE:
        card.column = KanbanColumn.W_TRAKCIE

    return card.column != prev


@router.get("", response_model=list[CardOut])
async def list_cards(
    session: AsyncSession = Depends(get_session),
    _: object = Depends(get_current_user),
) -> list[CardOut]:
    result = await session.execute(
        select(KanbanCard)
        .options(selectinload(KanbanCard.checklist))
        .order_by(KanbanCard.sort_order, KanbanCard.id)
    )
    cards = result.scalars().all()
    return await _serialize_cards(session, cards)


@router.post("", response_model=CardOut, status_code=status.HTTP_201_CREATED)
async def create_card(
    payload: CardCreate,
    session: AsyncSession = Depends(get_session),
    _: object = Depends(get_current_user),
) -> CardOut:
    equipment = await session.get(Equipment, payload.equipment_id)
    if not equipment:
        raise HTTPException(status_code=400, detail="Unknown equipment")
    if payload.rental_id is not None:
        rental = await session.get(Rental, payload.rental_id)
        if not rental:
            raise HTTPException(status_code=400, detail="Unknown rental")
    card = KanbanCard(
        equipment_id=payload.equipment_id,
        rental_id=payload.rental_id,
        title=payload.title,
        priority=payload.priority,
        due_date=payload.due_date,
        source=payload.source,
        assigned_worker=payload.assigned_worker,
        notes=payload.notes,
    )
    for idx, item in enumerate(payload.checklist):
        card.checklist.append(
            KanbanChecklistItem(label=item.label, sort_order=item.sort_order or idx)
        )
    session.add(card)
    await session.commit()
    card = await _card_with_checklist(session, card.id)

    await notify_mechaniks_new_card(session, card.title, equipment.code)
    await broadcaster.broadcast("card.created", {"id": card.id, "column": card.column.value})
    return (await _serialize_cards(session, [card]))[0]


@router.patch("/{card_id}", response_model=CardOut)
async def update_card(
    card_id: int,
    payload: CardUpdate,
    session: AsyncSession = Depends(get_session),
    _: object = Depends(get_current_user),
) -> CardOut:
    card = await _card_with_checklist(session, card_id)
    data = payload.model_dump(exclude_unset=True)

    explicit_column = "column" in data

    for k, v in data.items():
        setattr(card, k, v)

    if not explicit_column and "assigned_worker" in data and data["assigned_worker"]:
        if card.column == KanbanColumn.NA_SERWIS:
            card.column = KanbanColumn.W_TRAKCIE

    await session.commit()
    card = await _card_with_checklist(session, card_id)
    await broadcaster.broadcast("card.updated", {"id": card.id, "column": card.column.value})
    return (await _serialize_cards(session, [card]))[0]


@router.post("/{card_id}/checklist/{item_id}/toggle", response_model=CardOut)
async def toggle_checklist(
    card_id: int,
    item_id: int,
    done: bool,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> CardOut:
    item = await session.get(KanbanChecklistItem, item_id)
    if not item or item.card_id != card_id:
        raise HTTPException(status_code=404, detail="Item not found")
    item.done = done
    item.done_at = datetime.now(UTC) if done else None
    item.done_by_user_id = user.id if done else None
    await session.commit()

    card = await _card_with_checklist(session, card_id)
    moved = _auto_advance_column(card)
    if moved:
        await session.commit()
        card = await _card_with_checklist(session, card_id)

    await broadcaster.broadcast(
        "checklist.toggled",
        {
            "card_id": card_id,
            "item_id": item_id,
            "done": done,
            "by_user": user.name,
            "column": card.column.value,
        },
    )
    return (await _serialize_cards(session, [card]))[0]


@router.delete(
    "/{card_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(UserRole.MANAGER, UserRole.BIURO))],
)
async def delete_card(card_id: int, session: AsyncSession = Depends(get_session)) -> None:
    card = await session.get(KanbanCard, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Not found")
    await session.delete(card)
    await session.commit()
    await broadcaster.broadcast("card.deleted", {"id": card_id})
