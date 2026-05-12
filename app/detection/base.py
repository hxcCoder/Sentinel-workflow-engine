from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import AlertSeverity


# ── Base de Detección ──────────────────────────────────

@dataclass(slots=True)
class DetectionFinding:
    rule_id: str
    title: str
    description: str

    severity: AlertSeverity

    matched_at: datetime

    source: str

    evidence: Mapping[str, Any]


# ── Regla de Detección ─────────────────────────────────

class DetectionRule(ABC):
    rule_id: str
    title: str
    description: str

    severity: AlertSeverity

    source: str = "sentinellab"

    @abstractmethod
    async def evaluate(
        self,
        db: AsyncSession,
        start_time: datetime,
        end_time: datetime,
    ) -> list[DetectionFinding]:
        """
        Evalúa la regla dentro de una ventana temporal.
        """
        ...