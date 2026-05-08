"""CLI: python -m app.cli seed — наполнить БД дефолтными данными."""
import asyncio
import sys

from app.database import AsyncSessionLocal
from app.repositories.auth import AuthRepository
from app.repositories.equipment import EquipmentRepository
from app.services.seed_service import seed_all


async def _seed() -> None:
    async with AsyncSessionLocal() as session:
        await seed_all(AuthRepository(session), EquipmentRepository(session))
    print("Seed OK")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] != "seed":
        print("Usage: python -m app.cli seed")
        sys.exit(1)
    asyncio.run(_seed())


if __name__ == "__main__":
    main()
