"""
Наполнение БД:
- 18 категорий из KnowledgeTopKop.json
- стартовые пользователи, если PIN заданы через локальный .env
- Один exemplar: Kobelco mini 302 (для кейса Artur)
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import hash_pin
from app.models import (
    Equipment,
    EquipmentCategory,
    EquipmentStatus,
    TrackingType,
    User,
    UserRole,
)

PRIMARY_USERS: list[tuple[str, UserRole, str]] = [
    ("Biuro", UserRole.BIURO, "pin_default_biuro"),
    ("Dyrektor", UserRole.MANAGER, "pin_default_manager"),
]

CATEGORIES: list[tuple[str, str, TrackingType]] = [
    ("koparki", "Koparki", TrackingType.MTH),
    ("ladowarki", "Ładowarki", TrackingType.MTH),
    ("walce", "Walce", TrackingType.MTH),
    ("zageszczarki-wibratory", "Zagęszczarki i wibratory", TrackingType.DAILY_ONLY),
    ("mloty-narzedzia-pneumatyczne", "Młoty i narzędzia pneumatyczne", TrackingType.DAILY_ONLY),
    ("sprezarki-kompresory", "Sprężarki i kompresory", TrackingType.RBH),
    ("agregaty-pradotworcze", "Agregaty prądotwórcze", TrackingType.RBH),
    ("przecinarki-pily", "Przecinarki i piły", TrackingType.DAILY_ONLY),
    ("osuszanie-ogrzewanie", "Osuszanie i ogrzewanie", TrackingType.DAILY_ONLY),
    ("mycie", "Mycie", TrackingType.DAILY_ONLY),
    ("spawanie-plazma", "Spawanie i plazma", TrackingType.RBH),
    ("pompy", "Pompy", TrackingType.RBH),
    ("drabiny", "Drabiny", TrackingType.DAILY_ONLY),
    ("sprzet-tynki-podlogi", "Sprzęt do tynków i podłóg", TrackingType.DAILY_ONLY),
    ("sprzet-beton", "Sprzęt do betonu", TrackingType.DAILY_ONLY),
    ("osprzet-drogowy", "Osprzęt drogowy", TrackingType.DAILY_ONLY),
    ("przyczepy", "Przyczepy", TrackingType.DAILY_ONLY),
    ("szalunki", "Szalunki", TrackingType.DAILY_ONLY),
]


async def seed_categories(session: AsyncSession) -> None:
    existing = {c.slug for c in (await session.execute(select(EquipmentCategory))).scalars()}
    for idx, (slug, name, tracking) in enumerate(CATEGORIES):
        if slug in existing:
            continue
        session.add(EquipmentCategory(
            slug=slug, name_pl=name, default_tracking=tracking, sort_order=idx,
        ))
    await session.flush()


async def seed_users(session: AsyncSession) -> None:
    settings = get_settings()
    if not (settings.pin_default_biuro and settings.pin_default_manager):
        return

    existing = {
        user.name: user
        for user in (await session.execute(select(User))).scalars()
    }
    for name, role, pin_field in PRIMARY_USERS:
        pin = getattr(settings, pin_field)
        user = existing.get(name)
        if user is None:
            session.add(User(name=name, role=role, pin_hash=hash_pin(pin), is_active=True))
            continue
        user.role = role
        user.pin_hash = hash_pin(pin)
        user.is_active = True

    legacy_users = await session.execute(select(User).where(User.role == UserRole.MECHANIK))
    for user in legacy_users.scalars():
        user.is_active = False
    await session.flush()


async def seed_kobelco(session: AsyncSession) -> None:
    existing = await session.execute(select(Equipment).where(Equipment.code == "KOB-302"))
    if existing.scalar_one_or_none():
        return
    cat = await session.execute(
        select(EquipmentCategory).where(EquipmentCategory.slug == "koparki")
    )
    cat_row = cat.scalar_one_or_none()
    if cat_row is None:
        return
    session.add(
        Equipment(
            category_id=cat_row.id,
            code="KOB-302",
            name="Mini koparka Kobelco 302",
            manufacturer="Kobelco",
            model="SK30SR / 302",
            tracking_type=TrackingType.MTH,
            rate_tier_1_7=Decimal("500"),
            rate_above_7=Decimal("450"),
            daily_limit=10,
            overage_rate=Decimal("80"),
            status=EquipmentStatus.AVAILABLE,
        )
    )
    await session.flush()


async def seed_all(session: AsyncSession) -> None:
    await seed_categories(session)
    await seed_users(session)
    await seed_kobelco(session)
    await session.commit()
