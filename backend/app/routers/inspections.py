import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from pydantic import ValidationError

from app.core.deps import get_current_user
from app.models import Equipment, Inspection
from app.repositories.deps import get_inspection_repository
from app.repositories.inspections import InspectionRepository
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
    inspection_repository: InspectionRepository = Depends(get_inspection_repository),
    _: object = Depends(get_current_user),
) -> list[Inspection]:
    items = await inspection_repository.list_inspections()
    eq_ids = {i.equipment_id for i in items}
    eq_map = await inspection_repository.get_equipment_map(eq_ids)
    return [_attach_equipment(i, eq_map.get(i.equipment_id)) for i in items]


@router.get("/{inspection_id}", response_model=InspectionOut)
async def get_inspection(
    inspection_id: int,
    inspection_repository: InspectionRepository = Depends(get_inspection_repository),
    _: object = Depends(get_current_user),
) -> Inspection:
    item = await inspection_repository.get_inspection_with_photos(inspection_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    equipment = await inspection_repository.get_equipment(item.equipment_id)
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
    inspection_repository: InspectionRepository = Depends(get_inspection_repository),
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
        dupe = await inspection_repository.get_by_client_local_id(data.client_local_id)
        if dupe:
            eq = await inspection_repository.get_equipment(dupe.equipment_id)
            return _attach_equipment(dupe, eq)

    equipment = await inspection_repository.get_equipment(data.equipment_id)
    if not equipment:
        raise HTTPException(status_code=400, detail="Unknown equipment")

    signature_path = None
    if data.signature_data_url:
        try:
            signature_path = save_data_url(data.signature_data_url, "signatures")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    photo_records: list[tuple[str, str]] = []
    for idx, upload in enumerate(photos):
        slot = slots[idx] if idx < len(slots) else "extra"
        try:
            rel = await save_upload(upload, "photos")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        photo_records.append((str(slot), rel))

    inspection = await inspection_repository.create_inspection(
        data,
        signature_path=signature_path,
        photos=photo_records,
    )
    return _attach_equipment(inspection, equipment)


@router.get("/{inspection_id}/pdf")
async def inspection_pdf(
    inspection_id: int,
    inspection_repository: InspectionRepository = Depends(get_inspection_repository),
    _: object = Depends(get_current_user),
) -> Response:
    inspection = await inspection_repository.get_inspection_with_photos(inspection_id)
    if not inspection:
        raise HTTPException(status_code=404, detail="Not found")
    equipment = await inspection_repository.get_equipment(inspection.equipment_id)

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
