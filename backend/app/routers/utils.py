"""Utility endpoints: NIP lookup, client history and dashboard data."""
from __future__ import annotations

import logging
import re
from datetime import date, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user
from app.models import User
from app.repositories.deps import get_rental_repository
from app.repositories.rentals import RentalRepository

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
    rental_repository: RentalRepository = Depends(get_rental_repository),
    _: User = Depends(get_current_user),
) -> dict[str, object]:
    nip_clean = re.sub(r"[^0-9]", "", nip)
    if len(nip_clean) != _NIP_DIGITS:
        raise HTTPException(status_code=422, detail="NIP musi mieć 10 cyfr")

    existing = await rental_repository.get_latest_by_client_nip(nip_clean)
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
    rental_repository: RentalRepository = Depends(get_rental_repository),
    _: User = Depends(get_current_user),
) -> list[dict[str, str]]:
    rows = await rental_repository.list_client_history(q, _CLIENT_AUTOCOMPLETE_LIMIT)
    return [
        {"name": r.name, "nip": r.nip, "address": r.address, "phone": r.phone}
        for r in rows
    ]


@router.get("/dashboard")
async def dashboard(
    rental_repository: RentalRepository = Depends(get_rental_repository),
    _: User = Depends(get_current_user),
) -> dict[str, object]:
    today = date.today()
    month_start = today.replace(day=1)
    week_end = today + timedelta(days=_DASHBOARD_LOOKAHEAD_DAYS)

    summary = await rental_repository.get_dashboard_summary(
        today=today,
        month_start=month_start,
        week_end=week_end,
    )

    return {
        "active_rentals": summary.active_rentals,
        "equipment_out": summary.equipment_out,
        "ending_today": [
            {
                "id": r.id,
                "client_name": r.client_name,
                "end_date": str(r.end_date),
                "equipment_id": r.equipment_id,
            }
            for r in summary.ending_today
        ],
        "ending_week": summary.ending_week,
        "month_revenue": float(summary.month_revenue),
    }
