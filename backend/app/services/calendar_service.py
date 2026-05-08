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


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(CENTS, rounding=ROUND_HALF_UP)


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
