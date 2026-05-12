"""
Расчёт аренды: дни + сумма.

Две модели оплаты:
- Tier: 1-7 дни по одной ставке, 8-N по другой (стандарт TopKop)
- Flat: все дни по одной ставке (разовые договора типа Artur Kornak)

Переключатели:
- weekdays_only: считать только пн-пт
- align_to_monday: сдвинуть start на ближайший понедельник (для долгой аренды)

Все деньги — Decimal с ROUND_HALF_UP до 0.01.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

TIER_BREAKPOINT_DAYS = 7
CENTS = Decimal("0.01")


@dataclass(frozen=True)
class CalculationResult:
    days: int
    tier1_days: int
    tier2_days: int
    tier1_amount: Decimal
    tier2_amount: Decimal
    subtotal: Decimal
    adjustment_pct: Decimal
    adjustment_amount: Decimal
    total_netto: Decimal

    def as_dict(self) -> dict:
        return {
            "days": self.days,
            "tier1_days": self.tier1_days,
            "tier2_days": self.tier2_days,
            "tier1_amount": str(self.tier1_amount),
            "tier2_amount": str(self.tier2_amount),
            "subtotal": str(self.subtotal),
            "adjustment_pct": str(self.adjustment_pct),
            "adjustment_amount": str(self.adjustment_amount),
            "total_netto": str(self.total_netto),
        }


@dataclass(frozen=True)
class PricingResult:
    days: int
    tier1_days: int
    tier2_days: int
    tier1_amount: Decimal
    tier2_amount: Decimal
    subtotal: Decimal
    adjustment_pct: Decimal
    adjustment_amount: Decimal
    rental_amount: Decimal
    billable_quantity: Decimal
    transport_cost: Decimal
    total_netto: Decimal
    billing_mode: Literal["daily", "hourly"]

    def as_dict(self) -> dict:
        return {
            "days": self.days,
            "tier1_days": self.tier1_days,
            "tier2_days": self.tier2_days,
            "tier1_amount": str(self.tier1_amount),
            "tier2_amount": str(self.tier2_amount),
            "subtotal": str(self.subtotal),
            "adjustment_pct": str(self.adjustment_pct),
            "adjustment_amount": str(self.adjustment_amount),
            "rental_amount": str(self.rental_amount),
            "billable_quantity": str(self.billable_quantity),
            "transport_cost": str(self.transport_cost),
            "total_netto": str(self.total_netto),
            "billing_mode": self.billing_mode,
        }


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(CENTS, rounding=ROUND_HALF_UP)


def _non_negative(value: Decimal, field_name: str) -> Decimal:
    if value < 0:
        raise ValueError(f"{field_name} must be >= 0")
    return value


def calculate_rental_days(
    start: date,
    end: date,
    weekdays_only: bool = True,
    align_to_monday: bool = True,
) -> int:
    """Inclusive счёт дней между start и end."""
    if end < start:
        raise ValueError("end_date must be >= start_date")

    current = start
    if align_to_monday and current.weekday() != 0:
        days_ahead = (7 - current.weekday()) % 7
        current = current + timedelta(days=days_ahead)

    days = 0
    while current <= end:
        if not weekdays_only or current.weekday() < 5:
            days += 1
        current += timedelta(days=1)
    return days


def calculate_tiered_total(
    days: int,
    rate_tier_1_7: Decimal,
    rate_above_7: Decimal,
    discount_pct: Decimal = Decimal("0"),
    surcharge_pct: Decimal = Decimal("0"),
    flat_rate: bool = False,
) -> CalculationResult:
    """
    Подсчёт суммы брутто-нетто (без VAT).
    flat_rate=True → обе ставки трактуются как единая rate_tier_1_7.
    """
    if days < 0:
        raise ValueError("days must be >= 0")

    if flat_rate:
        effective_above = rate_tier_1_7
    else:
        effective_above = rate_above_7

    tier1_days = min(days, TIER_BREAKPOINT_DAYS)
    tier2_days = max(0, days - TIER_BREAKPOINT_DAYS)

    tier1_amount = Decimal(tier1_days) * rate_tier_1_7
    tier2_amount = Decimal(tier2_days) * effective_above
    subtotal = _quantize(tier1_amount + tier2_amount)

    adjustment_pct = surcharge_pct - discount_pct
    adjustment_amount = _quantize(subtotal * adjustment_pct / Decimal("100"))
    total_netto = _quantize(subtotal + adjustment_amount)

    return CalculationResult(
        days=days,
        tier1_days=tier1_days,
        tier2_days=tier2_days,
        tier1_amount=_quantize(tier1_amount),
        tier2_amount=_quantize(tier2_amount),
        subtotal=subtotal,
        adjustment_pct=adjustment_pct,
        adjustment_amount=adjustment_amount,
        total_netto=total_netto,
    )


def calculate_rental_pricing(
    *,
    days: int,
    rate_tier_1_7: Decimal,
    rate_above_7: Decimal,
    billing_mode: Literal["daily", "hourly"] = "daily",
    operator_hours: Decimal | None = None,
    hourly_rate: Decimal | None = None,
    transport_cost: Decimal = Decimal("0"),
    discount_pct: Decimal = Decimal("0"),
    surcharge_pct: Decimal = Decimal("0"),
    flat_rate: bool = False,
) -> PricingResult:
    transport = _quantize(_non_negative(transport_cost, "transport_cost"))

    if billing_mode == "daily":
        daily = calculate_tiered_total(
            days=days,
            rate_tier_1_7=rate_tier_1_7,
            rate_above_7=rate_above_7,
            discount_pct=discount_pct,
            surcharge_pct=surcharge_pct,
            flat_rate=flat_rate,
        )
        return PricingResult(
            days=daily.days,
            tier1_days=daily.tier1_days,
            tier2_days=daily.tier2_days,
            tier1_amount=daily.tier1_amount,
            tier2_amount=daily.tier2_amount,
            subtotal=daily.subtotal,
            adjustment_pct=daily.adjustment_pct,
            adjustment_amount=daily.adjustment_amount,
            rental_amount=daily.total_netto,
            billable_quantity=Decimal(daily.days),
            transport_cost=transport,
            total_netto=_quantize(daily.total_netto + transport),
            billing_mode="daily",
        )

    if billing_mode != "hourly":
        raise ValueError("billing_mode must be daily or hourly")
    if operator_hours is None or hourly_rate is None:
        raise ValueError("operator_hours and hourly_rate are required for hourly billing")

    hours = _quantize(_non_negative(operator_hours, "operator_hours"))
    rate = _quantize(_non_negative(hourly_rate, "hourly_rate"))
    subtotal = _quantize(hours * rate)
    adjustment_pct = surcharge_pct - discount_pct
    adjustment_amount = _quantize(subtotal * adjustment_pct / Decimal("100"))
    rental_amount = _quantize(subtotal + adjustment_amount)

    return PricingResult(
        days=days,
        tier1_days=0,
        tier2_days=0,
        tier1_amount=Decimal("0.00"),
        tier2_amount=Decimal("0.00"),
        subtotal=subtotal,
        adjustment_pct=adjustment_pct,
        adjustment_amount=adjustment_amount,
        rental_amount=rental_amount,
        billable_quantity=hours,
        transport_cost=transport,
        total_netto=_quantize(rental_amount + transport),
        billing_mode="hourly",
    )


def calculate_overage(
    meter_start: float | None,
    meter_end: float | None,
    days: int,
    daily_limit: int | None,
    overage_rate: Decimal | None,
) -> Decimal:
    """Доплата за превышение mth/rbh лимита. Возвращает 0 если данных нет."""
    if not daily_limit or not overage_rate or meter_start is None or meter_end is None:
        return Decimal("0.00")
    used = max(0.0, meter_end - meter_start)
    allowed = float(daily_limit * days)
    over = max(0.0, used - allowed)
    if over == 0:
        return Decimal("0.00")
    return _quantize(Decimal(str(over)) * overage_rate)
