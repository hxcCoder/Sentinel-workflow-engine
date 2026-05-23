from __future__ import annotations

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.schemas.alert import AlertFilters


class AlertRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        alert_id: str,
    ) -> Alert | None:
        result = await self.db.execute(
            select(Alert).where(Alert.id == alert_id)
        )

        return result.scalar_one_or_none()

    async def get_by_fingerprint(
        self,
        fingerprint: str,
    ) -> Alert | None:
        result = await self.db.execute(
            select(Alert).where(
                Alert.fingerprint == fingerprint
            )
        )

        return result.scalar_one_or_none()

    async def list_with_filters(
        self,
        filters: AlertFilters,
    ) -> list[Alert]:
        query = select(Alert)

        conditions = []

        if filters.status:
            conditions.append(Alert.status == filters.status)

        if filters.severity:
            conditions.append(Alert.severity == filters.severity)

        if filters.rule_id:
            conditions.append(Alert.rule_id == filters.rule_id)

        if filters.source:
            conditions.append(Alert.source == filters.source)

        if conditions:
            query = query.where(and_(*conditions))

        query = (
            query
            .order_by(Alert.last_seen.desc())
            .limit(filters.limit)
            .offset(filters.offset)
        )

        result = await self.db.execute(query)

        return list(result.scalars().all())
