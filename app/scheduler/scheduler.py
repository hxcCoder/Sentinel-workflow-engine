from __future__ import annotations

import logging
from typing import Any

from app.scheduler.jobs.detection_job import (
    get_last_detection_run,
    run_detection_cycle,
)

logger = logging.getLogger(__name__)

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
except ModuleNotFoundError:
    AsyncIOScheduler = None  # type: ignore[assignment]


_scheduler: Any | None = None


def start_scheduler() -> None:
    global _scheduler

    if AsyncIOScheduler is None:
        logger.warning(
            "APScheduler is not installed; detection scheduler disabled"
        )
        return

    if _scheduler and _scheduler.running:
        return

    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        run_detection_cycle,
        trigger="interval",
        minutes=5,
        id="detection_cycle",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=60,
    )
    _scheduler.start()

    logger.info("Detection scheduler started")


def shutdown_scheduler() -> None:
    global _scheduler

    if not _scheduler or not _scheduler.running:
        return

    _scheduler.shutdown(wait=False)
    logger.info("Detection scheduler stopped")


def get_scheduler_status() -> dict[str, Any]:
    return {
        "installed": AsyncIOScheduler is not None,
        "running": bool(_scheduler and _scheduler.running),
        "jobs": (
            [job.id for job in _scheduler.get_jobs()]
            if _scheduler and _scheduler.running
            else []
        ),
        "last_detection_run": (
            get_last_detection_run().isoformat()
            if get_last_detection_run()
            else None
        ),
    }
