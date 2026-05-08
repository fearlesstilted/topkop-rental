
from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_roles
from app.database import get_session
from app.models import Equipment, EquipmentCategory, Rental, UserRole
from app.models.enums import RentalStatus
from app.schemas.rental import (
    RentalCalcRequest,
    RentalCalcResponse,
    RentalCreate,
    RentalOut,
    RentalUpdate,
)
from app.services.calendar_service import calculate_rental_days, calculate_tiered_total
from app.services.pdf_service import render_rental_contract

_STATUS_TRANSITIONS: dict[RentalStatus, set[RentalStatus]] = {
    RentalStatus.DRAFT: {RentalStatus.ACTIVE, RentalStatus.CANCELLED},
    RentalStatus.ACTIVE: {RentalStatus.RETURNED, RentalStatus.CANCELLED},
    RentalStatus.RETURNED: set(),
    RentalStatus.CANCELLED: set(),
}
_RECALCULATED_FIELDS = {
    "start_date",
    "end_date",
    "weekdays_only",
    "align_to_monday",
    "rate_tier_1_7",
    "rate_above_7",
    "flat_rate",
    "discount_pct",
    "surcharge_pct",
}

router = APIRouter()


@router.post("/calculate", response_model=RentalCalcResponse)
async def calculate(
    payload: RentalCalcRequest,
    _: object = Depends(get_current_user),
) -> RentalCalcResponse:
    days = calculate_rental_days(
        payload.start_date, payload.end_date,
        weekdays_only=payload.weekdays_only,
        align_to_monday=payload.align_to_monday,
    )
    result = calculate_tiered_total(
        days=days,
        rate_tier_1_7=payload.rate_tier_1_7,
        rate_above_7=payload.rate_above_7,
        discount_pct=payload.discount_pct,
        surcharge_pct=payload.surcharge_pct,
        flat_rate=payload.flat_rate,
    )
    return RentalCalcResponse(**result.as_dict())


@router.get("", response_model=list[RentalOut])
async def list_rentals(
    session: AsyncSession = Depends(get_session),
    _: object = Depends(get_current_user),
) -> list[Rental]:
    result = await session.execute(select(Rental).order_by(Rental.created_at.desc()))
    return result.scalars().all()


@router.get("/{rental_id}", response_model=RentalOut)
async def get_rental(
    rental_id: int,
    session: AsyncSession = Depends(get_session),
    _: object = Depends(get_current_user),
) -> Rental:
    item = await session.get(Rental, rental_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item


@router.post(
    "",
    response_model=RentalOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.MANAGER, UserRole.BIURO))],
)
async def create_rental(
    payload: RentalCreate,
    session: AsyncSession = Depends(get_session),
) -> Rental:
    equipment = await session.get(Equipment, payload.equipment_id)
    if not equipment:
        raise HTTPException(status_code=400, detail="Unknown equipment")

    days = calculate_rental_days(
        payload.start_date, payload.end_date,
        weekdays_only=payload.weekdays_only,
        align_to_monday=payload.align_to_monday,
    )
    calc = calculate_tiered_total(
        days=days,
        rate_tier_1_7=payload.rate_tier_1_7,
        rate_above_7=payload.rate_above_7,
        discount_pct=payload.discount_pct,
        surcharge_pct=payload.surcharge_pct,
        flat_rate=payload.flat_rate,
    )

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
        rental_days=days,
        subtotal=calc.subtotal,
        total_netto=calc.total_netto,
        billing_entity=payload.billing_entity,
        notes=payload.notes,
    )
    session.add(rental)
    await session.commit()
    await session.refresh(rental)
    return rental


@router.patch(
    "/{rental_id}",
    response_model=RentalOut,
    dependencies=[Depends(require_roles(UserRole.MANAGER, UserRole.BIURO))],
)
async def update_rental(
    rental_id: int,
    payload: RentalUpdate,
    session: AsyncSession = Depends(get_session),
) -> Rental:
    item = await session.get(Rental, rental_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if item.status == RentalStatus.RETURNED:
        raise HTTPException(status_code=409, detail="Nie można edytować zakończonej umowy.")

    updated = payload.model_dump(exclude_unset=True)
    for k, v in updated.items():
        setattr(item, k, v)

    if updated.keys() & _RECALCULATED_FIELDS:
        days = calculate_rental_days(
            item.start_date, item.end_date,
            weekdays_only=item.weekdays_only,
            align_to_monday=item.align_to_monday,
        )
        calc = calculate_tiered_total(
            days=days,
            rate_tier_1_7=item.rate_tier_1_7,
            rate_above_7=item.rate_above_7,
            discount_pct=item.discount_pct,
            surcharge_pct=item.surcharge_pct,
            flat_rate=item.flat_rate,
        )
        item.rental_days = days
        item.subtotal = calc.subtotal
        item.total_netto = calc.total_netto

    await session.commit()
    await session.refresh(item)
    return item


@router.patch(
    "/{rental_id}/status",
    response_model=RentalOut,
    dependencies=[Depends(require_roles(UserRole.MANAGER, UserRole.BIURO))],
)
async def change_status(
    rental_id: int,
    new_status: RentalStatus = Body(..., embed=True),
    session: AsyncSession = Depends(get_session),
) -> Rental:
    item = await session.get(Rental, rental_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    allowed = _STATUS_TRANSITIONS.get(item.status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Niedozwolone przejście: {item.status.value} → {new_status.value}",
        )
    item.status = new_status
    await session.commit()
    await session.refresh(item)
    return item


@router.delete(
    "/{rental_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(UserRole.MANAGER, UserRole.BIURO))],
)
async def delete_rental(rental_id: int, session: AsyncSession = Depends(get_session)) -> None:
    item = await session.get(Rental, rental_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if item.status == RentalStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nie można usunąć aktywnej umowy. Najpierw anuluj lub zakończ najem.",
        )
    await session.delete(item)
    await session.commit()


@router.get("/{rental_id}/pdf")
async def rental_pdf(
    rental_id: int,
    session: AsyncSession = Depends(get_session),
    _: object = Depends(get_current_user),
) -> Response:
    rental = await session.get(Rental, rental_id)
    if not rental:
        raise HTTPException(status_code=404, detail="Not found")
    equipment = await session.get(Equipment, rental.equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    category = await session.get(EquipmentCategory, equipment.category_id)
    data, mime = await render_rental_contract(rental, equipment, category)
    filename = f"umowa_{rental.id}.{'pdf' if mime == 'application/pdf' else 'html'}"
    return Response(
        content=data,
        media_type=mime,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
