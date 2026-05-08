from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user, require_roles
from app.models import KanbanCard, User, UserRole
from app.models.enums import KanbanColumn
from app.repositories.deps import get_kanban_repository
from app.repositories.kanban import KanbanRepository
from app.schemas.kanban import CardCreate, CardOut, CardUpdate
from app.services.notification_service import notify_mechaniks_new_card
from app.services.ws_manager import broadcaster

router = APIRouter()


async def _card_with_checklist(
    kanban_repository: KanbanRepository,
    card_id: int,
) -> KanbanCard:
    card = await kanban_repository.get_card_with_checklist(card_id)
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
    kanban_repository: KanbanRepository = Depends(get_kanban_repository),
    _: object = Depends(get_current_user),
) -> list[KanbanCard]:
    return await kanban_repository.list_cards()


@router.post("", response_model=CardOut, status_code=status.HTTP_201_CREATED)
async def create_card(
    payload: CardCreate,
    kanban_repository: KanbanRepository = Depends(get_kanban_repository),
    _: object = Depends(get_current_user),
) -> KanbanCard:
    equipment = await kanban_repository.get_equipment(payload.equipment_id)
    if not equipment:
        raise HTTPException(status_code=400, detail="Unknown equipment")
    card = await kanban_repository.create_card(payload)

    await notify_mechaniks_new_card(card.title, equipment.code)
    await broadcaster.broadcast("card.created", {"id": card.id, "column": card.column.value})
    return card


@router.patch("/{card_id}", response_model=CardOut)
async def update_card(
    card_id: int,
    payload: CardUpdate,
    kanban_repository: KanbanRepository = Depends(get_kanban_repository),
    _: object = Depends(get_current_user),
) -> KanbanCard:
    card = await _card_with_checklist(kanban_repository, card_id)
    updated_fields = await kanban_repository.apply_card_update(card, payload)

    if (
        "column" not in updated_fields
        and "assigned_worker" in updated_fields
        and card.assigned_worker
    ):
        if card.column == KanbanColumn.NA_SERWIS:
            card.column = KanbanColumn.W_TRAKCIE

    card = await kanban_repository.save_card(card)
    await broadcaster.broadcast("card.updated", {"id": card.id, "column": card.column.value})
    return card


@router.post("/{card_id}/checklist/{item_id}/toggle", response_model=CardOut)
async def toggle_checklist(
    card_id: int,
    item_id: int,
    done: bool,
    kanban_repository: KanbanRepository = Depends(get_kanban_repository),
    user: User = Depends(get_current_user),
) -> KanbanCard:
    item = await kanban_repository.get_checklist_item(item_id)
    if not item or item.card_id != card_id:
        raise HTTPException(status_code=404, detail="Item not found")
    item.done = done
    item.done_at = datetime.now(UTC) if done else None
    item.done_by_user_id = user.id if done else None
    card = await _card_with_checklist(kanban_repository, card_id)

    _auto_advance_column(card)
    card = await kanban_repository.save_card(card)

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
    return card


@router.delete(
    "/{card_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(UserRole.MANAGER, UserRole.BIURO))],
)
async def delete_card(
    card_id: int,
    kanban_repository: KanbanRepository = Depends(get_kanban_repository),
) -> None:
    card = await kanban_repository.get_card_with_checklist(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Not found")
    await kanban_repository.delete_card(card)
    await broadcaster.broadcast("card.deleted", {"id": card_id})
