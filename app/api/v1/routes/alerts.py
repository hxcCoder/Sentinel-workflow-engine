from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_analyst
from app.db.session import get_db
from app.models.alert import (
    AlertSeverity,
    AlertStatus,
)
from app.models.user import User
from app.schemas.alert import (
    AlertFilters,
    AlertPublic,
    AlertUpdate,
)
from app.services.alert_service import AlertService

router = APIRouter(
    prefix="/alerts",
    tags=["alerts"],
)


@router.get(
    "/",
    response_model=list[AlertPublic],
)
async def list_alerts(
    status_filter: AlertStatus | None = None,
    severity: AlertSeverity | None = None,
    rule_id: str | None = None,
    source: str | None = None,

    limit: Annotated[
        int,
        Query(ge=1, le=500),
    ] = 50,

    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,

    db: AsyncSession = Depends(get_db),

    _: User = Depends(require_analyst),
):
    filters = AlertFilters(
        status=status_filter,
        severity=severity,
        rule_id=rule_id,
        source=source,
        limit=limit,
        offset=offset,
    )

    service = AlertService(db)

    return await service.list_alerts(filters)


@router.get(
    "/{alert_id}",
    response_model=AlertPublic,
)
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),

    _: User = Depends(require_analyst),
):
    service = AlertService(db)

    alert = await service.get_by_id(alert_id)

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    return alert


@router.patch(
    "/{alert_id}",
    response_model=AlertPublic,
)
async def update_alert(
    alert_id: str,
    data: AlertUpdate,

    db: AsyncSession = Depends(get_db),

    current_user: User = Depends(require_analyst),
):
    service = AlertService(db)

    alert = await service.get_by_id(alert_id)

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    updated = await service.update_alert(
        alert,
        data,
    )

    return updated