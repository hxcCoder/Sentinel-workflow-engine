from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate, UserPublic


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Registro ──────────────────────────────────────────────────────────────

    async def register(self, data: UserCreate) -> UserPublic:
        email = data.email.strip().lower()

        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        user = User(
            email=email,
            name=data.name,
            hashed_password=hash_password(data.password),
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return UserPublic.model_validate(user)

    # ── Login ─────────────────────────────────────────────────────────────────

    async def login(self, email: str, password: str) -> TokenResponse:
        email = email.strip().lower()

        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account disabled",
            )

        return await self._issue_tokens(user)

    # ── Refresh ───────────────────────────────────────────────────────────────

    async def refresh(self, raw_token: str) -> TokenResponse:
        token_hash = hash_refresh_token(raw_token)

        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        stored = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if (
            not stored
            or stored.revoked_at is not None
            or stored.expires_at < now
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        result = await self.db.execute(
            select(User).where(User.id == stored.user_id)
        )
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account disabled",
            )

        stored.revoked_at = now
        new_tokens = await self._issue_tokens(user)
        await self.db.commit()

        return new_tokens

    # ── Logout individual ─────────────────────────────────────────────────────

    async def revoke_refresh_token(self, raw_token: str) -> None:
        token_hash = hash_refresh_token(raw_token)

        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        stored = result.scalar_one_or_none()

        if stored and stored.revoked_at is None:
            stored.revoked_at = datetime.now(timezone.utc)
            await self.db.commit()

    # ── Logout global ─────────────────────────────────────────────────────────

    async def revoke_all_user_tokens(self, user_id: str) -> None:
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        tokens = result.scalars().all()
        now = datetime.now(timezone.utc)

        for token in tokens:
            token.revoked_at = now

        await self.db.commit()

    # ── Helper interno ────────────────────────────────────────────────────────

    async def _issue_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(user.id)

        raw_refresh = generate_refresh_token()
        refresh_token = RefreshToken(
            token_hash=hash_refresh_token(raw_refresh),
            user_id=user.id,
            expires_at=datetime.now(timezone.utc) + timedelta(
                days=settings.refresh_token_expire_days
            ),
        )

        self.db.add(refresh_token)

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
        )