from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog, AuditSeverity


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        event_type: str,
        severity: AuditSeverity = AuditSeverity.info,
        actor_id: str | None = None,
        actor_email: str | None = None,
        ip_address: str | None = None,
        resource: str | None = None,
        details: dict | None = None,
    ) -> AuditLog:
        event = AuditLog(
            event_type=event_type,
            severity=severity,
            actor_id=actor_id,
            actor_email=actor_email,
            ip_address=ip_address,
            resource=resource,
            details=details,
        )

        self.db.add(event)
        await self.db.flush()

        return event

    async def get_recent(
        self,
        limit: int = 50,
        actor_id: str | None = None,
        event_type: str | None = None,
    ) -> list[AuditLog]:
        limit = min(limit, 100)

        query = select(AuditLog).order_by(
            desc(AuditLog.created_at)
        )

        if actor_id:
            query = query.where(
                AuditLog.actor_id == actor_id
            )

        if event_type:
            query = query.where(
                AuditLog.event_type == event_type
            )

        query = query.limit(limit)

        result = await self.db.execute(query)

        return list(result.scalars().all())