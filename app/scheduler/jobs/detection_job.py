from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from app.db.session import AsyncSessionLocal
from app.detection.engine import DetectionEngine
from app.detection.rules.auth_bruteforce import AuthBruteforceRule
from app.detection.rules.suspicious_refresh import SuspiciousRefreshRule
from app.services.alert_service import AlertService

logger = logging.getLogger(__name__)

_last_run: datetime | None = None


def get_last_detection_run() -> datetime | None:
    return _last_run


async def run_detection_cycle() -> None:
    global _last_run

    end_time = datetime.now(timezone.utc)
    start_time = _last_run or end_time - timedelta(minutes=5)

    try:
        async with AsyncSessionLocal() as db:
            rules = [
                AuthBruteforceRule(threshold=5),
                SuspiciousRefreshRule(
                    threshold=8,
                    critical_threshold=20,
                ),
            ]

            engine = DetectionEngine(rules=rules)

            findings = await engine.run(
                db=db,
                start_time=start_time,
                end_time=end_time,
            )

            if findings:
                await AlertService(db).upsert_many(findings)

        _last_run = end_time

        logger.info(
            "Detection cycle completed",
            extra={
                "findings_count": len(findings),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
        )
    except Exception:
        logger.exception(
            "Detection cycle failed",
            extra={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
        )
