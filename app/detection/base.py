from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditSeverity

# ── Base de Detección ─────────────────────────────────────────────
@dataclass(slots=True)
class DetectionFinding:
    rule_id: str
    title: str
    severity: AuditSeverity
    matched_at: datetime
    evidence: Mapping[str, Any]

# ── Regla de Detección ─────────────────────────────────────────────
class DetectionRule(ABC):
    rule_id: str
    title: str
    description: str
    severity: AuditSeverity

    @abstractmethod
    async def evaluate(
        self,
        db: AsyncSession,
        start_time: datetime,
        end_time: datetime,
    ) -> list[DetectionFinding]:
        """
        Evaluate the rule against the database
        inside a time window.
        """
        ...