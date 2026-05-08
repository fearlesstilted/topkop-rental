"""
PDF генерация через Jinja2 + WeasyPrint.
Fallback: если WeasyPrint не может инициализироваться (Windows без GTK),
возвращается HTML-байты — удобно для dev.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import get_settings
from app.models.enums import BillingEntity

logger = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BACKEND_ROOT / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def resolve_company(entity: BillingEntity | str | None) -> dict[str, Any]:
    """Возвращает реквизиты выбранной юрсущности для шаблона договора."""
    s = get_settings()
    val = (
        entity.value
        if isinstance(entity, BillingEntity)
        else entity or BillingEntity.TOPKOP_JDG.value
    )
    if val == BillingEntity.TK_SPZOO.value:
        return {
            "kind": "spzoo",
            "name": s.company_spzoo_name,
            "short": s.company_spzoo_short,
            "address": s.company_spzoo_address,
            "nip": s.company_spzoo_nip,
            "krs": s.company_spzoo_krs,
            "regon": s.company_spzoo_regon,
            "phone": s.company_spzoo_phone,
            "email": s.company_spzoo_email,
        }
    return {
        "kind": "jdg",
        "name": s.company_jdg_name,
        "short": s.company_jdg_short,
        "address": s.company_jdg_address,
        "nip": s.company_jdg_nip,
        "krs": "",
        "regon": s.company_jdg_regon,
        "phone": s.company_jdg_phone,
        "email": s.company_jdg_email,
    }


def _render(template: str, context: dict[str, Any]) -> str:
    settings = get_settings()
    ctx = dict(context)
    ctx.setdefault(
        "company",
        {
            "name": settings.company_name,
            "address": settings.company_address,
            "nip": settings.company_nip,
            "phone": settings.company_phone,
            "email": settings.company_email,
        },
    )
    return _env.get_template(template).render(**ctx)


def _to_bytes(html_str: str) -> tuple[bytes, str]:
    """Returns (bytes, mime). Falls back to HTML if WeasyPrint is unavailable."""
    try:
        from weasyprint import HTML  # type: ignore
        pdf_bytes = HTML(string=html_str, base_url=str(TEMPLATES_DIR)).write_pdf()
        return pdf_bytes, "application/pdf"
    except (ImportError, OSError) as exc:
        logger.warning("WeasyPrint unavailable, returning HTML: %s", exc)
        return html_str.encode("utf-8"), "text/html"


async def render_pdf(template: str, context: dict[str, Any]) -> tuple[bytes, str]:
    html_str = _render(template, context)
    return await asyncio.to_thread(_to_bytes, html_str)


async def render_rental_contract(rental, equipment, category) -> tuple[bytes, str]:
    return await render_pdf(
        "umowa_najmu.html",
        {
            "rental": rental,
            "equipment": equipment,
            "category": category,
            "company": resolve_company(getattr(rental, "billing_entity", None)),
        },
    )


async def render_inspection_report(inspection, equipment, photos) -> tuple[bytes, str]:
    return await render_pdf(
        "protokol.html",
        {"inspection": inspection, "equipment": equipment, "photos": photos},
    )
