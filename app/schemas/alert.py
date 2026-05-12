from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ConfigDict

from app.models.alert import AlertSeverity, AlertStatus


class AlertPublic(BaseModel):
    id: str

    # ── Correlación ─────────────────────────────────────

    fingerprint: str
    source: str
    rule_id: str
    title: str
    description: str | None

    # ── Severidad ──────────────────────────────────────

    original_severity: AlertSeverity
    severity: AlertSeverity
    status: AlertStatus

    # ── Timeline ───────────────────────────────────────

    event_count: int
    first_seen: datetime
    last_seen: datetime
    last_rule_match: datetime
    resolved_at: datetime | None

    # ── Evidencia ──────────────────────────────────────

    evidence: dict[str, Any] | None

    # ── Threat Intel ───────────────────────────────────

    attack_tactic: str | None
    attack_technique: str | None
    tags: list[str] | None

    # ── Workflow SOC ───────────────────────────────────

    assigned_to: str | None
    resolution_notes: str | None

    # ── Auditoría ──────────────────────────────────────

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertUpdate(BaseModel):
    status: AlertStatus | None = None
    severity: AlertSeverity | None = None

    assigned_to: str | None = None
    resolution_notes: str | None = None

    attack_tactic: str | None = None
    attack_technique: str | None = None

    tags: list[str] | None = None


class AlertFilters(BaseModel):
    status: AlertStatus | None = None
    severity: AlertSeverity |None = None

    rule_id: str | None = None
    source: str | None = None

    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)