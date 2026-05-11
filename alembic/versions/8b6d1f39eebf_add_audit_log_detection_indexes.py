"""add audit log detection indexes

Revision ID: 8b6d1f39eebf
Revises: d5e914c3a171
Create Date: 2026-05-10 19:42:26.504585

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '8b6d1f39eebf'
down_revision: Union[str, Sequence[str], None] = 'd5e914c3a171'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_audit_logs_event_created",
        "audit_logs",
        ["event_type", "created_at"],
    )

    op.create_index(
        "ix_audit_logs_ip_created",
        "audit_logs",
        ["ip_address", "created_at"],
    )

    op.create_index(
        "ix_audit_logs_actor_created",
        "audit_logs",
        ["actor_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_audit_logs_actor_created",
        table_name="audit_logs",
    )

    op.drop_index(
        "ix_audit_logs_ip_created",
        table_name="audit_logs",
    )

    op.drop_index(
        "ix_audit_logs_event_created",
        table_name="audit_logs",
    )