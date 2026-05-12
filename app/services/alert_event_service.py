from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.alert_event import (
    AlertEvent,
    AlertEventType,
)


class AlertEventService:

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Crear evento de timeline ───────────────────────────

    async def record(
        self,
        alert: Alert,
        event_type: AlertEventType,
        message: str | None = None,
        created_by_user_id: str | None = None,
        snapshot: dict[str, Any] | None = None,
    ) -> AlertEvent:
        """
        Registra un evento histórico asociado a una alerta.
        Guarda un snapshot parcial del estado de la alerta
        para mantener trazabilidad y auditoría.
        """

        event = AlertEvent(
            alert_id=alert.id,
            event_type=event_type,
            message=message,
            created_by_user_id=created_by_user_id,
            snapshot=snapshot or self._build_snapshot(alert),
        )

        self.db.add(event)

        # Flush para obtener ID sin comprometer la transacción
        await self.db.flush()

        return event

    # ── Timeline completo ──────────────────────────────────

    async def get_timeline(
        self,
        alert_id: str,
    ) -> list[AlertEvent]:
        """
        Retorna todos los eventos históricos
        de una alerta ordenados cronológicamente.
        """

        result = await self.db.execute(
            select(AlertEvent)
            .where(AlertEvent.alert_id == alert_id)
            .order_by(AlertEvent.created_at.asc())
        )

        return list(result.scalars().all())

    # ── Snapshot helper ────────────────────────────────────

    def _build_snapshot(
        self,
        alert: Alert,
    ) -> dict[str, Any]:
        """
        Construye un snapshot consistente
        del estado actual de la alerta.
        """

        return {
            "alert_id": alert.id,
            "rule_id": alert.rule_id,
            "title": alert.title,
            "severity": alert.severity.value,
            "status": alert.status.value,
            "event_count": alert.event_count,
            "assigned_to": alert.assigned_to,
            "attack_tactic": alert.attack_tactic,
            "attack_technique": alert.attack_technique,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }