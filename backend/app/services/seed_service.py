"""
Наполнение БД:
- 18 категорий из KnowledgeTopKop.json
- стартовые пользователи, если PIN заданы через локальный .env
- Один exemplar: Kobelco mini 302 (для кейса Artur)
"""
from __future__ import annotations

from decimal import Decimal

from app.config import get_settings
from app.core.security import hash_pin
from app.models import EquipmentStatus, TrackingType, UserRole
from app.repositories.auth import AuthRepository
from app.repositories.equipment import EquipmentRepository

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


async def seed_categories(equipment_repository: EquipmentRepository) -> None:
    existing = await equipment_repository.list_category_slugs()
    for idx, (slug, name, tracking) in enumerate(CATEGORIES):
        if slug in existing:
            continue
        await equipment_repository.add_category(
            slug=slug,
            name_pl=name,
            default_tracking=tracking,
            sort_order=idx,
        )


async def seed_users(auth_repository: AuthRepository) -> None:
    settings = get_settings()
    if not (
        settings.pin_default_biuro
        and settings.pin_default_mechanik
        and settings.pin_default_manager
    ):
        return

    defaults = [
        ("Biuro", UserRole.BIURO, settings.pin_default_biuro),
        ("Serwis", UserRole.MECHANIK, settings.pin_default_mechanik),
        ("Dyrektor", UserRole.MANAGER, settings.pin_default_manager),
    ]
    existing = await auth_repository.list_user_names()
    for name, role, pin in defaults:
        if name in existing:
            continue
        await auth_repository.create_user(
            name=name,
            role=role,
            pin_hash=hash_pin(pin),
            is_active=True,
        )


async def seed_kobelco(equipment_repository: EquipmentRepository) -> None:
    if await equipment_repository.get_equipment_by_code("KOB-302"):
        return
    cat_row = await equipment_repository.get_category_by_slug("koparki")
    if cat_row is None:
        return
    await equipment_repository.add_equipment(
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


async def seed_all(
    auth_repository: AuthRepository,
    equipment_repository: EquipmentRepository,
) -> None:
    await seed_categories(equipment_repository)
    await seed_users(auth_repository)
    await seed_kobelco(equipment_repository)
    await equipment_repository.commit()
