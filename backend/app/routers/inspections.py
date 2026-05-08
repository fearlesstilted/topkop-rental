import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.database import get_session
from app.models import Equipment, Inspection, InspectionPhoto
from app.schemas.inspection import InspectionCreate, InspectionOut
from app.services.file_service import absolute_path, save_data_url, save_upload
from app.services.pdf_service import render_inspection_report

router = APIRouter()


def _attach_equipment(inspection: Inspection, equipment: Equipment | None) -> Inspection:
    inspection.equipment_code = equipment.code if equipment else None  # type: ignore[attr-defined]
    inspection.equipment_name = equipment.name if equipment else None  # type: ignore[attr-defined]
    return inspection


@router.get("", response_model=list[InspectionOut])
async def list_inspections(
    session: AsyncSession = Depends(get_session),
    _: object = Depends(get_current_user),
) -> list[Inspection]:
    result = await session.execute(
        select(Inspection).options(selectinload(Inspection.photos)).order_by(Inspection.created_at.desc())
    )
    items = result.scalars().all()
    eq_ids = {i.equipment_id for i in items}
    eq_map: dict[int, Equipment] = {}
    if eq_ids:
        eq_result = await session.execute(select(Equipment).where(Equipment.id.in_(eq_ids)))
        eq_map = {e.id: e for e in eq_result.scalars()}
    return [_attach_equipment(i, eq_map.get(i.equipment_id)) for i in items]


@router.get("/{inspection_id}", response_model=InspectionOut)
async def get_inspection(
    inspection_id: int,
    session: AsyncSession = Depends(get_session),
    _: object = Depends(get_current_user),
) -> Inspection:
    result = await session.execute(
        select(Inspection)
        .options(selectinload(Inspection.photos))
        .where(Inspection.id == inspection_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    equipment = await session.get(Equipment, item.equipment_id)
    return _attach_equipment(item, equipment)


@router.post(
    "",
    response_model=InspectionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_inspection(
    payload: str = Form(..., description="JSON of InspectionCreate"),
    photos: list[UploadFile] = File(default_factory=list),
    photo_slots: str = Form("[]", description="JSON array slots matching photos order"),
    session: AsyncSession = Depends(get_session),
    _: object = Depends(get_current_user),
) -> Inspection:
    try:
        data = InspectionCreate.model_validate_json(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid payload: {exc}") from exc
    try:
        slots = json.loads(photo_slots)
        if not isinstance(slots, list):
            raise ValueError("slots must be a list")
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Invalid photo_slots: {exc}") from exc

    if data.client_local_id:
        existing = await session.execute(
            select(Inspection)
            .options(selectinload(Inspection.photos))
            .where(Inspection.client_local_id == data.client_local_id)
        )
        dupe = existing.scalar_one_or_none()
        if dupe:
            eq = await session.get(Equipment, dupe.equipment_id)
            return _attach_equipment(dupe, eq)

    equipment = await session.get(Equipment, data.equipment_id)
    if not equipment:
        raise HTTPException(status_code=400, detail="Unknown equipment")

    signature_path = None
    if data.signature_data_url:
        try:
            signature_path = save_data_url(data.signature_data_url, "signatures")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    inspection = Inspection(
        equipment_id=data.equipment_id,
        rental_id=data.rental_id,
        type=data.type,
        meter_reading=data.meter_reading,
        lat=data.lat,
        lon=data.lon,
        gps_accuracy_m=data.gps_accuracy_m,
        signature_path=signature_path,
        client_signer_name=data.client_signer_name,
        notes=data.notes,
        client_local_id=data.client_local_id,
    )
    session.add(inspection)
    await session.flush()

    for idx, upload in enumerate(photos):
        slot = slots[idx] if idx < len(slots) else "extra"
        try:
            rel = await save_upload(upload, "photos")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        session.add(InspectionPhoto(inspection_id=inspection.id, slot=str(slot), path=rel))

    await session.commit()
    result = await session.execute(
        select(Inspection)
        .options(selectinload(Inspection.photos))
        .where(Inspection.id == inspection.id)
    )
    return _attach_equipment(result.scalar_one(), equipment)


@router.get("/{inspection_id}/pdf")
async def inspection_pdf(
    inspection_id: int,
    session: AsyncSession = Depends(get_session),
    _: object = Depends(get_current_user),
) -> Response:
    result = await session.execute(
        select(Inspection)
        .options(selectinload(Inspection.photos))
        .where(Inspection.id == inspection_id)
    )
    inspection = result.scalar_one_or_none()
    if not inspection:
        raise HTTPException(status_code=404, detail="Not found")
    equipment = await session.get(Equipment, inspection.equipment_id)

    photos_ctx = [
        {"slot": p.slot, "path": p.path, "abs_path": absolute_path(p.path)}
        for p in inspection.photos
    ]
    inspection.signature_abs_path = (  # type: ignore[attr-defined]
        absolute_path(inspection.signature_path) if inspection.signature_path else None
    )

    data, mime = await render_inspection_report(inspection, equipment, photos_ctx)
    filename = f"protokol_{inspection.id}.{'pdf' if mime == 'application/pdf' else 'html'}"
    return Response(
        content=data,
        media_type=mime,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
