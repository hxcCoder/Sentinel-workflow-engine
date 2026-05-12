from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.detection.base import (
    DetectionFinding,
    DetectionRule,
)
from app.models.alert import AlertSeverity
from app.models.audit_log import AuditLog


class AuthBruteforceRule(DetectionRule):
    rule_id = "AUTH_001"

    title = "Posible ataque de fuerza bruta"

    description = (
        "Detecta múltiples intentos "
        "fallidos de login desde "
        "la misma IP"
    )

    severity = AlertSeverity.high

    def __init__(
        self,
        threshold: int = 5,
    ) -> None:
        self.threshold = threshold

    async def evaluate(
        self,
        db: AsyncSession,
        start_time: datetime,
        end_time: datetime,
    ) -> list[DetectionFinding]:
        stmt = (
            select(
                AuditLog.ip_address,
                func.count(AuditLog.id).label(
                    "attempt_count"
                ),
            )
            .where(
                AuditLog.event_type
                == "auth.login_failed",
                AuditLog.created_at
                >= start_time,
                AuditLog.created_at
                <= end_time,
                AuditLog.ip_address.is_not(
                    None
                ),
            )
            .group_by(
                AuditLog.ip_address
            )
            .having(
                func.count(AuditLog.id)
                >= self.threshold
            )
        )

        result = await db.execute(stmt)

        findings: list[
            DetectionFinding
        ] = []

        matched_at = datetime.now(
            timezone.utc
        )

        for (
            ip_address,
            attempt_count,
        ) in result.all():
            findings.append(
                DetectionFinding(
                    rule_id=self.rule_id,
                    title=self.title,
                    severity=self.severity,
                    matched_at=matched_at,
                    evidence={
                        "ip_address": ip_address,
                        "failed_attempts": attempt_count,
                        "window_start": start_time.isoformat(),
                        "window_end": end_time.isoformat(),
                        "threshold": self.threshold,
                    },
                )
            )

        return findings