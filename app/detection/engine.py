import logging
from datetime import datetime
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.detection.base import (
    DetectionFinding,
    DetectionRule,
)

logger = logging.getLogger(__name__)

# ── Motor de Detección ─────────────────────────────────────────────
class DetectionEngine:
    def __init__(
        self,
        rules: Sequence[DetectionRule],
    ) -> None:
        self.rules = rules
    # Evaluar todas las reglas de detección en un rango de tiempo
    async def run(
        self,
        db: AsyncSession,
        start_time: datetime,
        end_time: datetime,
        # Dev note: We could add a callback here to report findings in real-time
    ) -> list[DetectionFinding]:
        all_findings: list[DetectionFinding] = []

        logger.info(
            "Detection engine started",
            extra={
                "rules_count": len(self.rules),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
        )

        for rule in self.rules:
            try:
                findings = await rule.evaluate(
                    db,
                    start_time,
                    end_time,
                )

                if findings:
                    logger.info(
                        "Detection rule matched",
                        extra={
                            "rule_id": rule.rule_id,
                            "findings_count": len(findings),
                        },
                    )

                all_findings.extend(findings)

            except Exception:
                logger.exception(
                    "Detection rule failed",
                    extra={
                        "rule_id": getattr(
                            rule,
                            "rule_id",
                            "unknown",
                        ),
                    },
                )

        return all_findings