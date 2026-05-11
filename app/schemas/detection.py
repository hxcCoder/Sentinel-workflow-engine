from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.audit_log import AuditSeverity


class DetectionFindingPublic(BaseModel):
    rule_id: str
    title: str
    severity: AuditSeverity
    matched_at: datetime
    evidence: dict[str, Any]