from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user, require_roles
from app.models import Equipment, EquipmentCategory, UserRole
from app.repositories.deps import get_equipment_repository
from app.repositories.equipment import EquipmentRepository
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
    equipment_repository: EquipmentRepository = Depends(get_equipment_repository),
    _: object = Depends(get_current_user),
) -> list[EquipmentCategory]:
    return await equipment_repository.list_categories()


@router.patch(
    "/categories/{cat_id}",
    response_model=CategoryOut,
    dependencies=[Depends(require_roles(UserRole.MANAGER, UserRole.BIURO))],
)
async def update_category(
    cat_id: int,
    payload: CategoryUpdate,
    equipment_repository: EquipmentRepository = Depends(get_equipment_repository),
) -> EquipmentCategory:
    item = await equipment_repository.get_category(cat_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return await equipment_repository.update_category(item, payload)


@router.post(
    "/categories",
    response_model=CategoryOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.MANAGER, UserRole.BIURO))],
)
async def create_category(
    payload: CategoryCreate,
    equipment_repository: EquipmentRepository = Depends(get_equipment_repository),
) -> EquipmentCategory:
    if await equipment_repository.get_category_by_slug(payload.slug):
        raise HTTPException(status_code=409, detail="Slug already exists")
    return await equipment_repository.create_category(payload)


@router.get("", response_model=list[EquipmentOut])
async def list_equipment(
    equipment_repository: EquipmentRepository = Depends(get_equipment_repository),
    category_id: int | None = None,
    _: object = Depends(get_current_user),
) -> list[Equipment]:
    return await equipment_repository.list_equipment(category_id)


@router.get("/{equipment_id}", response_model=EquipmentOut)
async def get_equipment(
    equipment_id: int,
    equipment_repository: EquipmentRepository = Depends(get_equipment_repository),
    _: object = Depends(get_current_user),
) -> Equipment:
    item = await equipment_repository.get_equipment(equipment_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item


@router.post(
    "",
    response_model=EquipmentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.MANAGER, UserRole.BIURO))],
)
async def create_equipment(
    payload: EquipmentCreate,
    equipment_repository: EquipmentRepository = Depends(get_equipment_repository),
) -> Equipment:
    cat = await equipment_repository.get_category(payload.category_id)
    if not cat:
        raise HTTPException(status_code=400, detail="Unknown category")
    if await equipment_repository.get_equipment_by_code(payload.code):
        raise HTTPException(status_code=409, detail="Code already exists")
    return await equipment_repository.create_equipment(payload)


@router.patch(
    "/{equipment_id}",
    response_model=EquipmentOut,
    dependencies=[Depends(require_roles(UserRole.MANAGER, UserRole.BIURO))],
)
async def update_equipment(
    equipment_id: int,
    payload: EquipmentUpdate,
    equipment_repository: EquipmentRepository = Depends(get_equipment_repository),
) -> Equipment:
    item = await equipment_repository.get_equipment(equipment_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return await equipment_repository.update_equipment(item, payload)


@router.delete(
    "/{equipment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(UserRole.MANAGER))],
)
async def delete_equipment(
    equipment_id: int,
    equipment_repository: EquipmentRepository = Depends(get_equipment_repository),
) -> None:
    item = await equipment_repository.get_equipment(equipment_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if await equipment_repository.has_active_rental(equipment_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nie można usunąć — sprzęt ma aktywną umowę najmu.",
        )
    await equipment_repository.delete_equipment(item)
