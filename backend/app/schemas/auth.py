from pydantic import BaseModel

from app.models.enums import UserRole


class LoginRequest(BaseModel):
    pin: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    role: UserRole


class MeResponse(BaseModel):
    id: int
    name: str
    role: UserRole
