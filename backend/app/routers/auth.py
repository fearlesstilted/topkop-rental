import logging
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.security import create_access_token, verify_pin
from app.database import get_session
from app.models import User
from app.schemas.auth import LoginRequest, LoginResponse, MeResponse

router = APIRouter()
logger = logging.getLogger("topkop.auth")

_failed: dict[str, list[float]] = defaultdict(list)
_MAX_ATTEMPTS = 5
_WINDOW_SEC = 300


def _check_rate_limit(ip: str) -> None:
    now = time.monotonic()
    attempts = [t for t in _failed[ip] if now - t < _WINDOW_SEC]
    _failed[ip] = attempts
    if len(attempts) >= _MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Zbyt wiele nieudanych prób. Odczekaj {_WINDOW_SEC // 60} minut.",
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> LoginResponse:
    ip = request.client.host if request.client else "unknown"
    _check_rate_limit(ip)

    result = await session.execute(select(User).where(User.is_active.is_(True)))
    for user in result.scalars():
        if verify_pin(payload.pin, user.pin_hash):
            _failed[ip].clear()
            logger.info("LOGIN OK user=%s ip=%s", user.name, ip)
            token = create_access_token(str(user.id), {"role": user.role.value})
            return LoginResponse(
                access_token=token, user_id=user.id, name=user.name, role=user.role,
            )

    _failed[ip].append(time.monotonic())
    logger.warning("LOGIN FAIL ip=%s attempts=%d", ip, len(_failed[ip]))
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nieprawidłowy PIN")


@router.get("/me", response_model=MeResponse)
async def me(user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(id=user.id, name=user.name, role=user.role)
