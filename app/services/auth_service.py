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
from app.models.audit_log import AuditSeverity
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate, UserPublic
from app.services.audit_service import AuditService


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit = AuditService(db)

    # ── Registro ─────────────────────────────────────────────────────────────

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

        await self.audit.log(
            event_type="auth.register",
            severity=AuditSeverity.info,
            actor_id=user.id,
            actor_email=user.email,
            resource="/api/v1/auth/register",
        )
        await self.db.commit()

        return UserPublic.model_validate(user)

    # ── Login ────────────────────────────────────────────────────────────────

    async def login(
        self,
        email: str,
        password: str,
        ip_address: str | None = None,
    ) -> TokenResponse:
        email = email.strip().lower()

        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(
            password,
            user.hashed_password,
        ):
            await self.audit.log(
                event_type="auth.login_failed",
                severity=AuditSeverity.warning,
                actor_email=email,
                ip_address=ip_address,
                resource="/api/v1/auth/login",
            )
            await self.db.commit()

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        if not user.is_active:
            await self.audit.log(
                event_type="auth.login_disabled",
                severity=AuditSeverity.warning,
                actor_id=user.id,
                actor_email=user.email,
                ip_address=ip_address,
                resource="/api/v1/auth/login",
            )
            await self.db.commit()

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account disabled",
            )

        await self.audit.log(
            event_type="auth.login",
            severity=AuditSeverity.info,
            actor_id=user.id,
            actor_email=user.email,
            ip_address=ip_address,
            resource="/api/v1/auth/login",
        )

        tokens = await self._issue_tokens(user)

        await self.db.commit()

        return tokens

    # ── Refresh ──────────────────────────────────────────────────────────────

    async def refresh(
        self,
        raw_token: str,
        ip_address: str | None = None,
    ) -> TokenResponse:
        token_hash = hash_refresh_token(raw_token)

        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash
            )
        )
        stored = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if (
            not stored
            or stored.revoked_at is not None
            or stored.expires_at < now
        ):
            await self.audit.log(
                event_type="auth.refresh_failed",
                severity=AuditSeverity.warning,
                ip_address=ip_address,
                resource="/api/v1/auth/refresh",
            )
            await self.db.commit()

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        result = await self.db.execute(
            select(User).where(User.id == stored.user_id)
        )
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            await self.audit.log(
                event_type="auth.refresh_disabled",
                severity=AuditSeverity.warning,
                actor_id=stored.user_id,
                ip_address=ip_address,
                resource="/api/v1/auth/refresh",
            )
            await self.db.commit()

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account disabled",
            )

        stored.revoked_at = now

        await self.audit.log(
            event_type="auth.refresh",
            severity=AuditSeverity.info,
            actor_id=user.id,
            actor_email=user.email,
            ip_address=ip_address,
            resource="/api/v1/auth/refresh",
        )

        tokens = await self._issue_tokens(user)

        await self.db.commit()

        return tokens

    # ── Logout individual ────────────────────────────────────────────────────

    async def revoke_refresh_token(
        self,
        raw_token: str,
        ip_address: str | None = None,
    ) -> None:
        token_hash = hash_refresh_token(raw_token)

        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash
            )
        )
        stored = result.scalar_one_or_none()

        if stored and stored.revoked_at is None:
            stored.revoked_at = datetime.now(timezone.utc)

            await self.audit.log(
                event_type="auth.logout",
                severity=AuditSeverity.info,
                actor_id=stored.user_id,
                ip_address=ip_address,
                resource="/api/v1/auth/logout",
            )

            await self.db.commit()

    # ── Logout global ────────────────────────────────────────────────────────

    async def revoke_all_user_tokens(
        self,
        user_id: str,
        ip_address: str | None = None,
    ) -> None:
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

        await self.audit.log(
            event_type="auth.logout_all",
            severity=AuditSeverity.info,
            actor_id=user_id,
            ip_address=ip_address,
            resource="/api/v1/auth/logout-all",
            details={"revoked_count": len(tokens)},
        )

        await self.db.commit()

    # ── Helper interno ───────────────────────────────────────────────────────

    async def _issue_tokens(
        self,
        user: User,
    ) -> TokenResponse:
        access_token = create_access_token(user.id)

        raw_refresh = generate_refresh_token()

        refresh_token = RefreshToken(
            token_hash=hash_refresh_token(raw_refresh),
            user_id=user.id,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.refresh_token_expire_days),
        )

        self.db.add(refresh_token)

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
        )