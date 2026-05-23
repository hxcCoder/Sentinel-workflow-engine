from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.alert_event import AlertEventType


class AlertEventPublic(BaseModel):
    id: str
    alert_id: str
    event_type: AlertEventType
    message: str | None
    snapshot: dict[str, Any] | None
    created_by_user_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
