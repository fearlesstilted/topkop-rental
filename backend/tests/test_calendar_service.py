from datetime import date
from decimal import Decimal

import pytest

from app.services.calendar_service import (
    calculate_overage,
    calculate_rental_days,
    calculate_tiered_total,
)


class TestCalculateRentalDays:
    def test_two_weeks_weekdays_only_from_monday(self):
        # 2026-04-20 (Mon) → 2026-05-03 (Sun) — Artur case: 10 рабочих дней
        days = calculate_rental_days(
            start=date(2026, 4, 20),
            end=date(2026, 5, 3),
            weekdays_only=True,
            align_to_monday=True,
        )
        assert days == 10

    def test_align_to_monday_shifts_wednesday_start(self):
        # Start Wed 2026-04-15 → align to Mon 2026-04-20
        days = calculate_rental_days(
            start=date(2026, 4, 15),
            end=date(2026, 4, 24),
            weekdays_only=True,
            align_to_monday=True,
        )
        # Mon 20, Tue 21, Wed 22, Thu 23, Fri 24 = 5
        assert days == 5

    def test_include_weekends(self):
        days = calculate_rental_days(
            start=date(2026, 4, 20),
            end=date(2026, 4, 26),
            weekdays_only=False,
            align_to_monday=False,
        )
        assert days == 7

    def test_single_day(self):
        days = calculate_rental_days(
            start=date(2026, 4, 20),
            end=date(2026, 4, 20),
            weekdays_only=True,
            align_to_monday=False,
        )
        assert days == 1

    def test_end_before_start_raises(self):
        with pytest.raises(ValueError):
            calculate_rental_days(date(2026, 4, 20), date(2026, 4, 19))


class TestCalculateTieredTotal:
    def test_artur_flat_rate_ten_days_450(self):
        # Artur: 10 рабочих дней по 450 flat = 4500
        result = calculate_tiered_total(
            days=10,
            rate_tier_1_7=Decimal("450"),
            rate_above_7=Decimal("450"),
            flat_rate=True,
        )
        assert result.total_netto == Decimal("4500.00")
        assert result.tier1_days == 7
        assert result.tier2_days == 3

    def test_tiered_first_week_only(self):
        # 5 дней по 350 zł = 1750
        result = calculate_tiered_total(
            days=5,
            rate_tier_1_7=Decimal("350"),
            rate_above_7=Decimal("300"),
        )
        assert result.total_netto == Decimal("1750.00")
        assert result.tier2_days == 0

    def test_tiered_crosses_breakpoint(self):
        # 10 дней: 7×350 + 3×300 = 2450 + 900 = 3350
        result = calculate_tiered_total(
            days=10,
            rate_tier_1_7=Decimal("350"),
            rate_above_7=Decimal("300"),
        )
        assert result.total_netto == Decimal("3350.00")

    def test_discount_10_pct(self):
        # 7×350 = 2450 − 10% = 2205
        result = calculate_tiered_total(
            days=7,
            rate_tier_1_7=Decimal("350"),
            rate_above_7=Decimal("300"),
            discount_pct=Decimal("10"),
        )
        assert result.total_netto == Decimal("2205.00")

    def test_surcharge_5_pct(self):
        result = calculate_tiered_total(
            days=7,
            rate_tier_1_7=Decimal("100"),
            rate_above_7=Decimal("100"),
            surcharge_pct=Decimal("5"),
        )
        # 700 + 5% = 735
        assert result.total_netto == Decimal("735.00")

    def test_zero_days(self):
        result = calculate_tiered_total(
            days=0,
            rate_tier_1_7=Decimal("450"),
            rate_above_7=Decimal("450"),
        )
        assert result.total_netto == Decimal("0.00")


class TestCalculateOverage:
    def test_no_limit_zero(self):
        assert calculate_overage(100, 200, 10, None, Decimal("50")) == Decimal("0.00")

    def test_within_limit_zero(self):
        # 10 mth/day × 10 days = 100 allowed, used 95
        assert calculate_overage(0, 95, 10, 10, Decimal("50")) == Decimal("0.00")

    def test_over_limit_charges(self):
        # used 120, allowed 100, over 20, rate 50 = 1000
        assert calculate_overage(0, 120, 10, 10, Decimal("50")) == Decimal("1000.00")

    def test_missing_meter_zero(self):
        assert calculate_overage(None, 120, 10, 10, Decimal("50")) == Decimal("0.00")
