from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_analyst
from app.db.session import get_db
from app.detection.engine import DetectionEngine
from app.detection.rules.auth_bruteforce import (
    AuthBruteforceRule,
)
from app.detection.rules.suspicious_refresh import (
    SuspiciousRefreshRule,
)
from app.models.user import User
from app.schemas.detection import (
    DetectionFindingPublic,
)

router = APIRouter(
    prefix="/detection",
    tags=["detection"],
)

_engine = DetectionEngine(
    rules=[
        AuthBruteforceRule(),
        SuspiciousRefreshRule(),
    ]
)


@router.post("/run")
async def run_detection(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_analyst),
    minutes: Annotated[
        int,
        Query(
            ge=1,
            le=1440,
            description="Detection time window in minutes",
        ),
    ] = 10,
):
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(
        minutes=minutes
    )

    findings = await _engine.run(
        db=db,
        start_time=start_time,
        end_time=end_time,
    )

    return {
        "findings_count": len(findings),
        "metadata": {
            "window_minutes": minutes,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        },
        "findings": [
            DetectionFindingPublic.model_validate(
                finding
            )
            for finding in findings
        ],
    }
