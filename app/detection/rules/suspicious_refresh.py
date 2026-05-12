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


class SuspiciousRefreshRule(DetectionRule):
    rule_id = "AUTH_002"

    title = "Actividad sospechosa de refresh tokens"

    description = (
        "Detecta múltiples eventos "
        "auth.refresh desde una misma IP "
        "y reporta la cantidad de cuentas "
        "afectadas"
    )

    severity = AlertSeverity.medium

    def __init__(
        self,
        threshold: int = 8,
        critical_threshold: int = 20,
    ) -> None:
        self.threshold = threshold
        self.critical_threshold = critical_threshold

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
                    "refresh_count"
                ),
                func.count(
                    func.distinct(
                        AuditLog.actor_id
                    )
                ).label(
                    "distinct_users"
                ),
            )
            .where(
                AuditLog.event_type
                == "auth.refresh",

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
            refresh_count,
            distinct_users,
        ) in result.all():

            severity = (
                AlertSeverity.critical
                if refresh_count
                >= self.critical_threshold
                else self.severity
            )

            findings.append(
                DetectionFinding(
                    rule_id=self.rule_id,
                    title=self.title,
                    severity=severity,
                    matched_at=matched_at,
                    evidence={
                        "ip_address": ip_address,
                        "refresh_count": refresh_count,
                        "affected_users_count": distinct_users,
                        "window_start": start_time.isoformat(),
                        "window_end": end_time.isoformat(),
                        "threshold": self.threshold,
                        "critical_threshold": (
                            self.critical_threshold
                        ),
                        "is_multi_user_attack": (
                            distinct_users > 1
                        ),
                    },
                )
            )

        return findings