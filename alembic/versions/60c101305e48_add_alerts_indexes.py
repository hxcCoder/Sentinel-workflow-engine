from typing import Sequence, Union

from alembic import op


# revision identifiers
revision: str = "60c101305e48"
down_revision: Union[str, Sequence[str], None] = "43bcd5d9516d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_alerts_status_severity",
        "alerts",
        ["status", "severity"],
    )

    op.create_index(
        "ix_alerts_rule_last_seen",
        "alerts",
        ["rule_id", "last_seen"],
    )

    op.create_index(
        "ix_alert_events_alert_created",
        "alert_events",
        ["alert_id", "created_at"],
    )

    op.create_index(
        "ix_alert_events_type_created",
        "alert_events",
        ["event_type", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_alert_events_type_created",
        table_name="alert_events",
    )

    op.drop_index(
        "ix_alert_events_alert_created",
        table_name="alert_events",
    )

    op.drop_index(
        "ix_alerts_rule_last_seen",
        table_name="alerts",
    )

    op.drop_index(
        "ix_alerts_status_severity",
        table_name="alerts",
    )