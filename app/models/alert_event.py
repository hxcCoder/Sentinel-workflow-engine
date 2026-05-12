from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
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


class AlertEventType(str, enum.Enum):
    created = "created"

    updated = "updated"

    severity_changed = "severity_changed"

    status_changed = "status_changed"

    acknowledged = "acknowledged"

    reopened = "reopened"

    resolved = "resolved"

    false_positive = "false_positive"

    evidence_added = "evidence_added"


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # ── Relación ──────────────────────────────────────────

    alert_id: Mapped[str] = mapped_column(
        ForeignKey(
            "alerts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # ── Evento ────────────────────────────────────────────

    event_type: Mapped[AlertEventType] = mapped_column(
        SAEnum(AlertEventType),
        nullable=False,
        index=True,
    )

    message: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    # ── Snapshot histórico ────────────────────────────────

    snapshot: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # ── Actor ─────────────────────────────────────────────

    created_by_user_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True,
    )

    # ── Metadata ──────────────────────────────────────────

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # ── ORM ───────────────────────────────────────────────

    alert = relationship(
        "Alert",
        back_populates="timeline",
    )