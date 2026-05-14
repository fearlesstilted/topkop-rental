from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_roles
from app.database import get_session
from app.models import Equipment, EquipmentCategory, Rental, UserRole
from app.models.enums import RentalStatus
from app.schemas.equipment import (
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    EquipmentCreate,
    EquipmentOut,
    EquipmentUpdate,
)

router = APIRouter()


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(
    session: AsyncSession = Depends(get_session),
    _: object = Depends(get_current_user),
) -> list[EquipmentCategory]:
    result = await session.execute(
        select(EquipmentCategory).order_by(EquipmentCategory.sort_order, EquipmentCategory.name_pl)
    )
    return result.scalars().all()


@router.patch(
    "/categories/{cat_id}",
    response_model=CategoryOut,
    dependencies=[Depends(require_roles(UserRole.BIURO))],
)
async def update_category(
    cat_id: int,
    payload: CategoryUpdate,
    session: AsyncSession = Depends(get_session),
) -> EquipmentCategory:
    item = await session.get(EquipmentCategory, cat_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    await session.commit()
    await session.refresh(item)
    return item


@router.post(
    "/categories",
    response_model=CategoryOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.BIURO))],
)
async def create_category(
    payload: CategoryCreate,
    session: AsyncSession = Depends(get_session),
) -> EquipmentCategory:
    existing = await session.execute(
        select(EquipmentCategory).where(EquipmentCategory.slug == payload.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Slug already exists")
    cat = EquipmentCategory(**payload.model_dump())
    session.add(cat)
    await session.commit()
    await session.refresh(cat)
    return cat


@router.get("", response_model=list[EquipmentOut])
async def list_equipment(
    session: AsyncSession = Depends(get_session),
    category_id: int | None = None,
    _: object = Depends(get_current_user),
) -> list[Equipment]:
    stmt = select(Equipment).order_by(Equipment.code)
    if category_id is not None:
        stmt = stmt.where(Equipment.category_id == category_id)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{equipment_id}", response_model=EquipmentOut)
async def get_equipment(
    equipment_id: int,
    session: AsyncSession = Depends(get_session),
    _: object = Depends(get_current_user),
) -> Equipment:
    item = await session.get(Equipment, equipment_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item


@router.post(
    "",
    response_model=EquipmentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.BIURO))],
)
async def create_equipment(
    payload: EquipmentCreate,
    session: AsyncSession = Depends(get_session),
) -> Equipment:
    cat = await session.get(EquipmentCategory, payload.category_id)
    if not cat:
        raise HTTPException(status_code=400, detail="Unknown category")
    exists = await session.execute(select(Equipment).where(Equipment.code == payload.code))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Code already exists")
    item = Equipment(**payload.model_dump())
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


@router.patch(
    "/{equipment_id}",
    response_model=EquipmentOut,
    dependencies=[Depends(require_roles(UserRole.BIURO))],
)
async def update_equipment(
    equipment_id: int,
    payload: EquipmentUpdate,
    session: AsyncSession = Depends(get_session),
) -> Equipment:
    item = await session.get(Equipment, equipment_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    await session.commit()
    await session.refresh(item)
    return item


@router.delete(
    "/{equipment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(UserRole.BIURO))],
)
async def delete_equipment(equipment_id: int, session: AsyncSession = Depends(get_session)) -> None:
    item = await session.get(Equipment, equipment_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    active = await session.execute(
        select(Rental).where(
            Rental.equipment_id == equipment_id,
            Rental.status == RentalStatus.ACTIVE,
        )
    )
    if active.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nie można usunąć — sprzęt ma aktywną umowę najmu.",
        )
    await session.delete(item)
    await session.commit()
