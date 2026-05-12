from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.detection.base import DetectionFinding

from app.models.alert import (
    Alert,
    AlertSeverity,
    AlertStatus,
)

from app.models.alert_event import (
    AlertEventType,
)

from app.schemas.alert import AlertUpdate

from app.services.alert_event_service import (
    AlertEventService,
)


class AlertService:

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Fingerprint ─────────────────────────────────────────

    def _make_fingerprint(
        self,
        finding: DetectionFinding,
    ) -> str:
        target = (
            finding.evidence.get("ip_address")
            or finding.evidence.get("actor_id")
            or "unknown"
        )

        raw = f"{finding.rule_id}:{target}"

        return hashlib.sha256(raw.encode()).hexdigest()

    # ── Severidad ───────────────────────────────────────────

    def _max_severity(
        self,
        current: AlertSeverity,
        incoming: AlertSeverity,
    ) -> AlertSeverity:
        order = {
            AlertSeverity.low: 1,
            AlertSeverity.medium: 2,
            AlertSeverity.high: 3,
            AlertSeverity.critical: 4,
        }

        return (
            incoming
            if order[incoming] > order[current]
            else current
        )

    # ── Upsert individual ───────────────────────────────────

    async def upsert(
        self,
        finding: DetectionFinding,
    ) -> Alert:
        fingerprint = self._make_fingerprint(finding)

        now = datetime.now(timezone.utc)

        result = await self.db.execute(
            select(Alert).where(
                Alert.fingerprint == fingerprint
            )
        )

        existing = result.scalar_one_or_none()

        # ── Existing alert ──────────────────────────────────

        if existing:
            if existing.status == AlertStatus.false_positive:
                return existing

            existing.event_count += 1
            existing.last_seen = now
            existing.last_rule_match = finding.matched_at
            existing.updated_at = now

            existing.severity = self._max_severity(
                existing.severity,
                finding.severity,
            )

            existing.evidence = dict(finding.evidence)

            history = existing.raw_findings or []

            history.append({
                "matched_at": finding.matched_at.isoformat(),
                "severity": finding.severity.value,
                "evidence": dict(finding.evidence),
            })

            existing.raw_findings = history[-50:]

            await AlertEventService(self.db).record(
                alert=existing,
                event_type=AlertEventType.updated,
                message="Alert updated from detection engine",
            )

            await self.db.flush()

            return existing

        # ── New alert ───────────────────────────────────────

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
            evidence=dict(finding.evidence),
            raw_findings=[
                {
                    "matched_at": finding.matched_at.isoformat(),
                    "severity": finding.severity.value,
                    "evidence": dict(finding.evidence),
                }
            ],
        )

        self.db.add(alert)

        await self.db.flush()

        await AlertEventService(self.db).record(
            alert=alert,
            event_type=AlertEventType.created,
            message="Alert created from detection engine",
        )

        return alert

    # ── Bulk upsert ─────────────────────────────────────────

    async def upsert_many(
        self,
        findings: list[DetectionFinding],
    ) -> list[Alert]:
        alerts: list[Alert] = []

        for finding in findings:
            alert = await self.upsert(finding)
            alerts.append(alert)

        await self.db.commit()

        return alerts

    # ── Query single ────────────────────────────────────────

    async def get_by_id(
        self,
        alert_id: str,
    ) -> Alert | None:
        result = await self.db.execute(
            select(Alert).where(Alert.id == alert_id)
        )

        return result.scalar_one_or_none()

    # ── Query multiple ──────────────────────────────────────

    async def get_many(
        self,
        status: AlertStatus | None = None,
        severity: AlertSeverity | None = None,
        rule_id: str | None = None,
        source: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Alert]:
        query = select(Alert)

        conditions = []

        if status:
            conditions.append(Alert.status == status)

        if severity:
            conditions.append(Alert.severity == severity)

        if rule_id:
            conditions.append(Alert.rule_id == rule_id)

        if source:
            conditions.append(Alert.source == source)

        if conditions:
            query = query.where(and_(*conditions))

        query = (
            query
            .order_by(Alert.last_seen.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)

        return list(result.scalars().all())

    # ── Update generic ──────────────────────────────────────

    async def update(
        self,
        alert_id: str,
        data: AlertUpdate,
    ) -> Alert | None:
        alert = await self.get_by_id(alert_id)

        if not alert:
            return None

        now = datetime.now(timezone.utc)

        updates = data.model_dump(exclude_none=True)

        for field, value in updates.items():
            setattr(alert, field, value)

        if data.status in (
            AlertStatus.resolved,
            AlertStatus.false_positive,
        ):
            alert.resolved_at = now

        alert.updated_at = now

        await AlertEventService(self.db).record(
            alert=alert,
            event_type=AlertEventType.updated,
            message="Alert updated manually",
        )

        await self.db.commit()

        await self.db.refresh(alert)

        return alert

    # ── Lifecycle: acknowledge ─────────────────────────────

    async def acknowledge(
        self,
        alert: Alert,
        user_id: str,
    ) -> Alert:
        if alert.status == AlertStatus.in_progress:
            return alert

        if alert.status in (
            AlertStatus.resolved,
            AlertStatus.false_positive,
        ):
            raise ValueError(
                "Cannot acknowledge closed alert"
            )

        now = datetime.now(timezone.utc)

        alert.status = AlertStatus.in_progress
        alert.updated_at = now

        await AlertEventService(self.db).record(
            alert=alert,
            event_type=AlertEventType.acknowledged,
            message="Alert acknowledged",
            created_by_user_id=user_id,
        )

        await self.db.commit()

        await self.db.refresh(alert)

        return alert

    # ── Lifecycle: resolve ─────────────────────────────────

    async def resolve(
        self,
        alert: Alert,
        user_id: str,
        notes: str | None = None,
    ) -> Alert:
        if alert.status in (
            AlertStatus.resolved,
            AlertStatus.false_positive,
        ):
            return alert

        now = datetime.now(timezone.utc)

        alert.status = AlertStatus.resolved
        alert.resolved_at = now
        alert.updated_at = now

        if notes:
            alert.resolution_notes = notes

        await AlertEventService(self.db).record(
            alert=alert,
            event_type=AlertEventType.resolved,
            message=notes or "Alert resolved",
            created_by_user_id=user_id,
        )

        await self.db.commit()

        await self.db.refresh(alert)

        return alert

    # ── Lifecycle: false positive ──────────────────────────

    async def mark_false_positive(
        self,
        alert: Alert,
        user_id: str,
        notes: str | None = None,
    ) -> Alert:
        if alert.status == AlertStatus.false_positive:
            return alert

        now = datetime.now(timezone.utc)

        alert.status = AlertStatus.false_positive
        alert.resolved_at = now
        alert.updated_at = now

        if notes:
            alert.resolution_notes = notes

        await AlertEventService(self.db).record(
            alert=alert,
            event_type=AlertEventType.false_positive,
            message=notes or "Marked as false positive",
            created_by_user_id=user_id,
        )

        await self.db.commit()

        await self.db.refresh(alert)

        return alert

    # ── Lifecycle: reopen ──────────────────────────────────

    async def reopen(
        self,
        alert: Alert,
        user_id: str,
    ) -> Alert:
        if alert.status in (
            AlertStatus.open,
            AlertStatus.in_progress,
        ):
            return alert

        now = datetime.now(timezone.utc)

        alert.status = AlertStatus.open
        alert.resolved_at = None
        alert.updated_at = now

        await AlertEventService(self.db).record(
            alert=alert,
            event_type=AlertEventType.reopened,
            message="Alert reopened",
            created_by_user_id=user_id,
        )

        await self.db.commit()

        await self.db.refresh(alert)

        return alert