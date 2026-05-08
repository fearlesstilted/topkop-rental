from fastapi import APIRouter, Body, Depends, HTTPException, Response, status

from app.core.deps import get_current_user, require_roles
from app.models import Rental, UserRole
from app.models.enums import RentalStatus
from app.repositories.deps import get_rental_repository
from app.repositories.rentals import RentalRepository
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
    rental_repository: RentalRepository = Depends(get_rental_repository),
    _: object = Depends(get_current_user),
) -> list[Rental]:
    return await rental_repository.list_rentals()


@router.get("/{rental_id}", response_model=RentalOut)
async def get_rental(
    rental_id: int,
    rental_repository: RentalRepository = Depends(get_rental_repository),
    _: object = Depends(get_current_user),
) -> Rental:
    item = await rental_repository.get_rental(rental_id)
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
    rental_repository: RentalRepository = Depends(get_rental_repository),
) -> Rental:
    equipment = await rental_repository.get_equipment(payload.equipment_id)
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

    return await rental_repository.create_rental(
        payload,
        rental_days=days,
        subtotal=calc.subtotal,
        total_netto=calc.total_netto,
    )


@router.patch(
    "/{rental_id}",
    response_model=RentalOut,
    dependencies=[Depends(require_roles(UserRole.MANAGER, UserRole.BIURO))],
)
async def update_rental(
    rental_id: int,
    payload: RentalUpdate,
    rental_repository: RentalRepository = Depends(get_rental_repository),
) -> Rental:
    item = await rental_repository.get_rental(rental_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if item.status == RentalStatus.RETURNED:
        raise HTTPException(status_code=409, detail="Nie można edytować zakończonej umowy.")

    updated_fields = await rental_repository.update_rental_fields(item, payload)

    if updated_fields & _RECALCULATED_FIELDS:
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

    return await rental_repository.save_rental(item)


@router.patch(
    "/{rental_id}/status",
    response_model=RentalOut,
    dependencies=[Depends(require_roles(UserRole.MANAGER, UserRole.BIURO))],
)
async def change_status(
    rental_id: int,
    new_status: RentalStatus = Body(..., embed=True),
    rental_repository: RentalRepository = Depends(get_rental_repository),
) -> Rental:
    item = await rental_repository.get_rental(rental_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    allowed = _STATUS_TRANSITIONS.get(item.status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Niedozwolone przejście: {item.status.value} → {new_status.value}",
    )
    item.status = new_status
    return await rental_repository.save_rental(item)


@router.delete(
    "/{rental_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(UserRole.MANAGER, UserRole.BIURO))],
)
async def delete_rental(
    rental_id: int,
    rental_repository: RentalRepository = Depends(get_rental_repository),
) -> None:
    item = await rental_repository.get_rental(rental_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    if item.status == RentalStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nie można usunąć aktywnej umowy. Najpierw anuluj lub zakończ najem.",
        )
    await rental_repository.delete_rental(item)


@router.get("/{rental_id}/pdf")
async def rental_pdf(
    rental_id: int,
    rental_repository: RentalRepository = Depends(get_rental_repository),
    _: object = Depends(get_current_user),
) -> Response:
    rental = await rental_repository.get_rental(rental_id)
    if not rental:
        raise HTTPException(status_code=404, detail="Not found")
    equipment = await rental_repository.get_equipment(rental.equipment_id)
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    category = await rental_repository.get_category(equipment.category_id)
    data, mime = await render_rental_contract(rental, equipment, category)
    filename = f"umowa_{rental.id}.{'pdf' if mime == 'application/pdf' else 'html'}"
    return Response(
        content=data,
        media_type=mime,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
