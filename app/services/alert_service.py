from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.detection.base import DetectionFinding
from app.models.alert import (
    Alert,
    AlertSeverity,
    AlertStatus,
)


class AlertService:

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Fingerprint ─────────────────────────────────────────

    def _make_fingerprint(
        self,
        finding: DetectionFinding,
    ) -> str:
        """
        Genera un fingerprint estable para
        correlacionar eventos similares.
        """

        target = (
            finding.evidence.get("ip_address")
            or finding.evidence.get("actor_id")
            or "unknown"
        )

        raw = f"{finding.rule_id}:{target}"

        return hashlib.sha256(
            raw.encode()
        ).hexdigest()

    # ── Severidad ───────────────────────────────────────────

    def _max_severity(
        self,
        current: AlertSeverity,
        incoming: AlertSeverity,
    ) -> AlertSeverity:
        """
        Mantiene la severidad más alta.
        """

        order = {
            AlertSeverity.low: 1,
            AlertSeverity.medium: 2,
            AlertSeverity.high: 3,
            AlertSeverity.critical: 4,
        }

        return (
            incoming
            if order[incoming]
            > order[current]
            else current
        )

    # ── Upsert individual ───────────────────────────────────

    async def upsert(
        self,
        finding: DetectionFinding,
    ) -> Alert:

        fingerprint = self._make_fingerprint(
            finding
        )

        now = datetime.now(
            timezone.utc
        )

        result = await self.db.execute(
            select(Alert).where(
                Alert.fingerprint
                == fingerprint
            )
        )

        existing = (
            result.scalar_one_or_none()
        )

        # ── Update ──────────────────────────────────────────

        if existing:

            # No reabrir false positives automáticamente
            if existing.status == AlertStatus.false_positive:
                return existing

            existing.event_count += 1

            existing.last_seen = now

            existing.last_rule_match = (
                finding.matched_at
            )

            existing.updated_at = now

            # Escalado automático
            existing.severity = (
                self._max_severity(
                    existing.severity,
                    finding.severity,
                )
            )

            # Mantener evidencia más reciente
            existing.evidence = dict(
                finding.evidence
            )

            # Agregar finding histórico
            history = (
                existing.raw_findings or []
            )

            history.append(
                {
                    "matched_at": finding.matched_at.isoformat(),
                    "severity": finding.severity.value,
                    "evidence": dict(
                        finding.evidence
                    ),
                }
            )

            # Limitar crecimiento infinito
            existing.raw_findings = history[-50:]

            await self.db.flush()

            return existing

        # ── Create ──────────────────────────────────────────

        alert = Alert(
            fingerprint=fingerprint,

            source="sentinellab",

            rule_id=finding.rule_id,

            title=finding.title,

            original_severity=finding.severity,

            severity=finding.severity,

            status=AlertStatus.open,

            event_count=1,

            first_seen=now,

            last_seen=now,

            last_rule_match=finding.matched_at,

            evidence=dict(
                finding.evidence
            ),

            raw_findings=[
                {
                    "matched_at": finding.matched_at.isoformat(),
                    "severity": finding.severity.value,
                    "evidence": dict(
                        finding.evidence
                    ),
                }
            ],
        )

        self.db.add(alert)

        await self.db.flush()

        return alert

    # ── Bulk upsert ─────────────────────────────────────────

    async def upsert_many(
        self,
        findings: list[DetectionFinding],
    ) -> list[Alert]:

        alerts: list[Alert] = []

        for finding in findings:
            alert = await self.upsert(
                finding
            )
            alerts.append(alert)

        await self.db.commit()

        return alerts