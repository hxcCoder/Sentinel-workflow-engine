from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)
from app.schemas.user import UserCreate, UserPublic
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService(db).register(data)


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService(db).login(
        data.email,
        data.password,
        ip_address=request.client.host if request.client else None,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh(
    data: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService(db).refresh(
        data.refresh_token,
        ip_address=request.client.host if request.client else None,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout(
    data: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await AuthService(db).revoke_refresh_token(
        data.refresh_token,
        ip_address=request.client.host if request.client else None,
    )


@router.get(
    "/me",
    response_model=UserPublic,
)
async def me(
    current_user: User = Depends(get_current_user),
):
    return current_user