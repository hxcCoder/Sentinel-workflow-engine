from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel

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
from app.schemas.alert_event import AlertEventPublic
from app.services.alert_event_service import AlertEventService
from app.services.alert_service import AlertService

router = APIRouter(
    prefix="/alerts",
    tags=["alerts"],
)


class AlertLifecycleRequest(BaseModel):
    notes: str | None = None


@router.get(
    "/",
    response_model=list[AlertPublic],
)
async def list_alerts(
    status_filter: Annotated[
        AlertStatus | None,
        Query(alias="status"),
    ] = None,
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

    _: User = Depends(require_analyst),
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


@router.post(
    "/{alert_id}/acknowledge",
    response_model=AlertPublic,
)
async def acknowledge_alert(
    alert_id: str,
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

    try:
        return await service.acknowledge(
            alert=alert,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{alert_id}/resolve",
    response_model=AlertPublic,
)
async def resolve_alert(
    alert_id: str,
    data: AlertLifecycleRequest | None = None,
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

    return await service.resolve(
        alert=alert,
        user_id=current_user.id,
        notes=data.notes if data else None,
    )


@router.post(
    "/{alert_id}/false-positive",
    response_model=AlertPublic,
)
async def mark_alert_false_positive(
    alert_id: str,
    data: AlertLifecycleRequest | None = None,
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

    return await service.mark_false_positive(
        alert=alert,
        user_id=current_user.id,
        notes=data.notes if data else None,
    )


@router.post(
    "/{alert_id}/reopen",
    response_model=AlertPublic,
)
async def reopen_alert(
    alert_id: str,
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

    return await service.reopen(
        alert=alert,
        user_id=current_user.id,
    )


@router.get(
    "/{alert_id}/timeline",
    response_model=list[AlertEventPublic],
)
async def get_alert_timeline(
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

    return await AlertEventService(db).get_timeline(alert_id)
