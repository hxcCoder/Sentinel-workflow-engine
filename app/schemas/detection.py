from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict

from app.models.alert import AlertSeverity


class DetectionFindingPublic(BaseModel):
    rule_id: str

    title: str
    description: str

    severity: AlertSeverity

    matched_at: datetime

    source: str

    evidence: Mapping[str, Any]

    model_config = ConfigDict(
        from_attributes=True
    )