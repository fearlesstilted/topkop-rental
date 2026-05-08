from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import BillingEntity, RentalStatus


class RentalCalcRequest(BaseModel):
    start_date: date
    end_date: date
    weekdays_only: bool = True
    align_to_monday: bool = True
    rate_tier_1_7: Decimal
    rate_above_7: Decimal
    flat_rate: bool = False
    discount_pct: Decimal = Decimal("0")
    surcharge_pct: Decimal = Decimal("0")


class RentalCalcResponse(BaseModel):
    days: int
    tier1_days: int
    tier2_days: int
    tier1_amount: Decimal
    tier2_amount: Decimal
    subtotal: Decimal
    adjustment_pct: Decimal
    adjustment_amount: Decimal
    total_netto: Decimal


class RentalCreate(BaseModel):
    equipment_id: int
    client_name: str = Field(min_length=1, max_length=200)
    client_nip: str | None = None
    client_address: str | None = None
    client_phone: str | None = None
    start_date: date
    end_date: date
    weekdays_only: bool = True
    align_to_monday: bool = True
    rate_tier_1_7: Decimal
    rate_above_7: Decimal
    flat_rate: bool = False
    daily_limit: int | None = None
    overage_rate: Decimal | None = None
    discount_pct: Decimal = Decimal("0")
    surcharge_pct: Decimal = Decimal("0")
    billing_entity: BillingEntity = BillingEntity.TOPKOP_JDG
    notes: str | None = None


class RentalUpdate(BaseModel):
    client_name: str | None = Field(default=None, min_length=1, max_length=200)
    client_nip: str | None = None
    client_address: str | None = None
    client_phone: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    weekdays_only: bool | None = None
    align_to_monday: bool | None = None
    rate_tier_1_7: Decimal | None = None
    rate_above_7: Decimal | None = None
    flat_rate: bool | None = None
    daily_limit: int | None = None
    overage_rate: Decimal | None = None
    discount_pct: Decimal | None = None
    surcharge_pct: Decimal | None = None
    billing_entity: BillingEntity | None = None
    notes: str | None = None


class RentalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    equipment_id: int
    client_name: str
    client_nip: str | None
    client_address: str | None
    client_phone: str | None
    start_date: date
    end_date: date
    weekdays_only: bool
    align_to_monday: bool
    rate_tier_1_7: Decimal
    rate_above_7: Decimal
    flat_rate: bool
    daily_limit: int | None
    overage_rate: Decimal | None
    discount_pct: Decimal
    surcharge_pct: Decimal
    rental_days: int
    subtotal: Decimal
    total_netto: Decimal
    status: RentalStatus
    billing_entity: BillingEntity
    notes: str | None
    pdf_path: str | None
