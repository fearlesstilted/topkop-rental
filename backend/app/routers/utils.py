"""Utility endpoints: NIP lookup, client history and dashboard data."""
from __future__ import annotations

import logging
import re
from datetime import date, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_session
from app.models import Equipment, Rental, User
from app.models.enums import EquipmentStatus, RentalBillingMode, RentalStatus, UserRole

logger = logging.getLogger(__name__)
router = APIRouter()

_MF_URL = "https://wl-api.mf.gov.pl/api/search/nip/{nip}?date={date}"
_MF_API_TIMEOUT_SEC = 10
_NIP_DIGITS = 10
_CLIENT_AUTOCOMPLETE_LIMIT = 20
_DASHBOARD_LOOKAHEAD_DAYS = 7


async def _mf_lookup(nip: str) -> dict[str, str] | None:
    url = _MF_URL.format(nip=nip, date=date.today().isoformat())
    async with httpx.AsyncClient(timeout=_MF_API_TIMEOUT_SEC) as client:
        r = await client.get(url)
    if r.status_code != 200:
        return None
    try:
        subject = r.json()["result"]["subject"]
    except (KeyError, TypeError):
        return None
    if not subject:
        return None

    name = subject.get("name", "")
    address = subject.get("residenceAddress") or subject.get("workingAddress") or ""

    return {"name": name, "address": address, "nip": nip}


@router.get("/nip/{nip}")
async def lookup_nip(
    nip: str,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> dict[str, object]:
    nip_clean = re.sub(r"[^0-9]", "", nip)
    if len(nip_clean) != _NIP_DIGITS:
        raise HTTPException(status_code=422, detail="NIP musi mieć 10 cyfr")

    result = await session.execute(
        select(Rental)
        .where(Rental.client_nip == nip_clean)
        .order_by(Rental.created_at.desc())
        .limit(1)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return {
            "source": "local",
            "name": existing.client_name,
            "address": existing.client_address or "",
            "phone": existing.client_phone or "",
            "nip": nip_clean,
        }

    try:
        data = await _mf_lookup(nip_clean)
    except httpx.HTTPError as e:
        logger.warning("MF lookup error: %s", e)
        raise HTTPException(
            status_code=502,
            detail="Błąd połączenia z API Ministerstwa Finansów",
        ) from e

    if not data or not data.get("name"):
        raise HTTPException(status_code=404, detail="Nie znaleziono firmy o podanym NIP")

    return {"source": "mf", "phone": "", **data}


@router.get("/clients")
async def list_clients(
    q: str = "",
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[dict[str, str]]:
    stmt = select(
        Rental.client_name,
        Rental.client_nip,
        Rental.client_address,
        Rental.client_phone,
    ).distinct(Rental.client_nip, Rental.client_name)

    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(Rental.client_name.ilike(like), Rental.client_nip.ilike(like))
        )

    stmt = stmt.order_by(Rental.client_name).limit(_CLIENT_AUTOCOMPLETE_LIMIT)
    rows = (await session.execute(stmt)).all()
    return [
        {"name": r.client_name, "nip": r.client_nip or "",
         "address": r.client_address or "", "phone": r.client_phone or ""}
        for r in rows
    ]


@router.get("/dashboard")
async def dashboard(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict[str, object]:
    today = date.today()
    month_start = today.replace(day=1)
    week_end = today + timedelta(days=_DASHBOARD_LOOKAHEAD_DAYS)

    active_rentals = (await session.execute(
        select(func.count()).where(Rental.status == RentalStatus.ACTIVE)
    )).scalar_one()

    equipment_out = (await session.execute(
        select(func.count()).where(Equipment.status == EquipmentStatus.RENTED)
    )).scalar_one()

    ending_today = (await session.execute(
        select(Rental).where(Rental.status == RentalStatus.ACTIVE, Rental.end_date == today)
    )).scalars().all()

    ending_week = (await session.execute(
        select(func.count()).where(
            Rental.status == RentalStatus.ACTIVE,
            Rental.end_date > today,
            Rental.end_date <= week_end,
        )
    )).scalar_one()

    month_revenue = (await session.execute(
        select(func.coalesce(func.sum(Rental.total_netto), 0)).where(
            Rental.status.in_([RentalStatus.ACTIVE, RentalStatus.RETURNED]),
            Rental.start_date >= month_start,
        )
    )).scalar_one()

    data: dict[str, object] = {
        "active_rentals": active_rentals,
        "equipment_out": equipment_out,
        "ending_today": [
            {
                "id": r.id,
                "client_name": r.client_name,
                "end_date": str(r.end_date),
                "equipment_id": r.equipment_id,
            }
            for r in ending_today
        ],
        "ending_week": ending_week,
        "month_revenue": float(month_revenue),
    }

    if user.role != UserRole.MANAGER:
        return data

    total_equipment = (await session.execute(
        select(func.count()).select_from(Equipment)
    )).scalar_one()
    available_equipment = (await session.execute(
        select(func.count()).where(Equipment.status == EquipmentStatus.AVAILABLE)
    )).scalar_one()
    service_equipment = (await session.execute(
        select(func.count()).where(Equipment.status == EquipmentStatus.SERVICE)
    )).scalar_one()
    broken_equipment = (await session.execute(
        select(func.count()).where(Equipment.status == EquipmentStatus.BROKEN)
    )).scalar_one()

    draft_rentals = (await session.execute(
        select(func.count()).where(Rental.status == RentalStatus.DRAFT)
    )).scalar_one()
    returned_month = (await session.execute(
        select(func.count()).where(
            Rental.status == RentalStatus.RETURNED,
            Rental.start_date >= month_start,
        )
    )).scalar_one()
    cancelled_month = (await session.execute(
        select(func.count()).where(
            Rental.status == RentalStatus.CANCELLED,
            Rental.start_date >= month_start,
        )
    )).scalar_one()
    hourly_rentals_month = (await session.execute(
        select(func.count()).where(
            Rental.billing_mode == RentalBillingMode.HOURLY,
            Rental.start_date >= month_start,
        )
    )).scalar_one()
    daily_rentals_month = (await session.execute(
        select(func.count()).where(
            Rental.billing_mode == RentalBillingMode.DAILY,
            Rental.start_date >= month_start,
        )
    )).scalar_one()
    operator_hours_month = (await session.execute(
        select(func.coalesce(func.sum(Rental.operator_hours), 0)).where(
            Rental.start_date >= month_start,
            Rental.operator_hours.is_not(None),
        )
    )).scalar_one()
    transport_revenue_month = (await session.execute(
        select(func.coalesce(func.sum(Rental.transport_cost), 0)).where(
            Rental.start_date >= month_start,
        )
    )).scalar_one()
    average_rental_netto = (await session.execute(
        select(func.coalesce(func.avg(Rental.total_netto), 0)).where(
            Rental.start_date >= month_start,
            Rental.status.in_([RentalStatus.ACTIVE, RentalStatus.RETURNED]),
        )
    )).scalar_one()

    upcoming_returns = (await session.execute(
        select(Rental)
        .where(
            Rental.status == RentalStatus.ACTIVE,
            Rental.end_date >= today,
            Rental.end_date <= week_end,
        )
        .order_by(Rental.end_date, Rental.client_name)
        .limit(6)
    )).scalars().all()

    top_clients = (await session.execute(
        select(
            Rental.client_name,
            func.coalesce(func.sum(Rental.total_netto), 0).label("total_netto"),
            func.count(Rental.id).label("rentals_count"),
        )
        .where(
            Rental.start_date >= month_start,
            Rental.status.in_([RentalStatus.ACTIVE, RentalStatus.RETURNED]),
        )
        .group_by(Rental.client_name)
        .order_by(func.sum(Rental.total_netto).desc())
        .limit(5)
    )).all()

    data.update({
        "total_equipment": total_equipment,
        "available_equipment": available_equipment,
        "service_equipment": service_equipment,
        "broken_equipment": broken_equipment,
        "draft_rentals": draft_rentals,
        "returned_month": returned_month,
        "cancelled_month": cancelled_month,
        "hourly_rentals_month": hourly_rentals_month,
        "daily_rentals_month": daily_rentals_month,
        "operator_hours_month": float(operator_hours_month),
        "transport_revenue_month": float(transport_revenue_month),
        "average_rental_netto": float(average_rental_netto),
        "upcoming_returns": [
            {"id": r.id, "client_name": r.client_name, "end_date": str(r.end_date)}
            for r in upcoming_returns
        ],
        "top_clients": [
            {
                "client_name": row.client_name,
                "total_netto": float(row.total_netto),
                "rentals_count": row.rentals_count,
            }
            for row in top_clients
        ],
    })
    return data
