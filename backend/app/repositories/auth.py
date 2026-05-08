from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active_users(self) -> list[User]:
        result = await self._session.execute(select(User).where(User.is_active.is_(True)))
        return list(result.scalars())

    async def get_active_user_by_id(self, user_id: int) -> User | None:
        result = await self._session.execute(
            select(User).where(User.id == user_id, User.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def list_user_names(self) -> set[str]:
        result = await self._session.execute(select(User.name))
        return set(result.scalars())

    async def create_user(
        self,
        *,
        name: str,
        role: UserRole,
        pin_hash: str,
        is_active: bool = True,
    ) -> User:
        user = User(name=name, role=role, pin_hash=pin_hash, is_active=is_active)
        self._session.add(user)
        await self._session.flush()
        return user

    async def commit(self) -> None:
        await self._session.commit()
