from collections.abc import AsyncGenerator

from app.database import AsyncSessionLocal
from app.repositories.auth import AuthRepository
from app.repositories.equipment import EquipmentRepository
from app.repositories.inspections import InspectionRepository
from app.repositories.kanban import KanbanRepository
from app.repositories.rentals import RentalRepository


async def get_auth_repository() -> AsyncGenerator[AuthRepository, None]:
    async with AsyncSessionLocal() as session:
        yield AuthRepository(session)


async def get_equipment_repository() -> AsyncGenerator[EquipmentRepository, None]:
    async with AsyncSessionLocal() as session:
        yield EquipmentRepository(session)


async def get_inspection_repository() -> AsyncGenerator[InspectionRepository, None]:
    async with AsyncSessionLocal() as session:
        yield InspectionRepository(session)


async def get_kanban_repository() -> AsyncGenerator[KanbanRepository, None]:
    async with AsyncSessionLocal() as session:
        yield KanbanRepository(session)


async def get_rental_repository() -> AsyncGenerator[RentalRepository, None]:
    async with AsyncSessionLocal() as session:
        yield RentalRepository(session)


async def get_seed_repositories() -> AsyncGenerator[
    tuple[AuthRepository, EquipmentRepository],
    None,
]:
    async with AsyncSessionLocal() as session:
        yield AuthRepository(session), EquipmentRepository(session)
