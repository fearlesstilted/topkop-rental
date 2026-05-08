from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EquipmentStatus, TrackingType


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    name_pl: str
    default_tracking: TrackingType
    sort_order: int


class CategoryCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=64)
    name_pl: str = Field(min_length=1, max_length=120)
    default_tracking: TrackingType = TrackingType.DAILY_ONLY
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name_pl: str | None = Field(default=None, min_length=1, max_length=120)
    default_tracking: TrackingType | None = None
    sort_order: int | None = None


class EquipmentBase(BaseModel):
    category_id: int
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=150)
    manufacturer: str | None = None
    model: str | None = None
    year: int | None = None
    registration_number: str | None = None
    tracking_type: TrackingType = TrackingType.DAILY_ONLY
    rate_tier_1_7: Decimal
    rate_above_7: Decimal
    daily_limit: int | None = None
    overage_rate: Decimal | None = None
    notes: str | None = None


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    year: int | None = None
    registration_number: str | None = None
    tracking_type: TrackingType | None = None
    rate_tier_1_7: Decimal | None = None
    rate_above_7: Decimal | None = None
    daily_limit: int | None = None
    overage_rate: Decimal | None = None
    status: EquipmentStatus | None = None
    notes: str | None = None


class EquipmentOut(EquipmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: EquipmentStatus
