from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    Integer,
    JSON,
    String,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.alert_event import AlertEvent


class AlertSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AlertStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    false_positive = "false_positive"


class Alert(Base):
    __tablename__ = "alerts"

    # ── Identidad ──────────────────────────────────────────

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ── Correlación ────────────────────────────────────────

    fingerprint: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    rule_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    # ── Severidad ──────────────────────────────────────────

    original_severity: Mapped[AlertSeverity] = mapped_column(
        SAEnum(AlertSeverity),
        nullable=False,
    )

    severity: Mapped[AlertSeverity] = mapped_column(
        SAEnum(AlertSeverity),
        nullable=False,
        index=True,
    )

    status: Mapped[AlertStatus] = mapped_column(
        SAEnum(AlertStatus),
        default=AlertStatus.open,
        nullable=False,
        index=True,
    )

    # ── Timeline / Estado ──────────────────────────────────

    event_count: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    last_rule_match: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── Evidencia ──────────────────────────────────────────

    evidence: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    raw_findings: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # ── Threat Intel / MITRE ───────────────────────────────

    tags: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    attack_tactic: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    attack_technique: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # ── Workflow SOC ───────────────────────────────────────

    assigned_to: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
    )

    resolution_notes: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )

    # ── Auditoría ──────────────────────────────────────────

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────

    timeline: Mapped[list["AlertEvent"]] = relationship(
        "AlertEvent",
        back_populates="alert",
        cascade="all, delete-orphan",
        order_by="AlertEvent.created_at",
    )