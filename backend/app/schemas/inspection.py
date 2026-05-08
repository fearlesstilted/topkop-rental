from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import InspectionType


class InspectionPhotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slot: str
    path: str


class InspectionCreate(BaseModel):
    equipment_id: int
    rental_id: int | None = None
    type: InspectionType
    meter_reading: float | None = None
    lat: float | None = None
    lon: float | None = None
    gps_accuracy_m: float | None = None
    signature_data_url: str | None = None
    client_signer_name: str | None = None
    notes: str | None = None
    client_local_id: str | None = None


class InspectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    equipment_id: int
    equipment_code: str | None = None
    equipment_name: str | None = None
    rental_id: int | None
    type: InspectionType
    meter_reading: float | None
    lat: float | None
    lon: float | None
    gps_accuracy_m: float | None
    signature_path: str | None
    client_signer_name: str | None
    notes: str | None
    pdf_path: str | None
    client_local_id: str | None
    created_at: datetime
    photos: list[InspectionPhotoOut] = Field(default_factory=list)
