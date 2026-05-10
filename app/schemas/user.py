from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}