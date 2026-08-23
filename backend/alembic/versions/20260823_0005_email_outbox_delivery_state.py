"""add persistent email outbox delivery state

Revision ID: 20260823_0005
Revises: 20260822_0004
Create Date: 2026-08-23
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260823_0005"
down_revision: str | None = "20260822_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "email_outbox",
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "email_outbox",
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE email_outbox "
            "SET processing_started_at = updated_at "
            "WHERE status = 'processing' AND processing_started_at IS NULL"
        )
    )
    op.create_check_constraint(
        "ck_email_outbox_processing_started_state",
        "email_outbox",
        "(status = 'processing' AND processing_started_at IS NOT NULL) "
        "OR (status != 'processing' AND processing_started_at IS NULL)",
    )
    op.create_index(
        "ix_email_outbox_status_next_attempt_id",
        "email_outbox",
        ["status", "next_attempt_at", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_email_outbox_status_next_attempt_id", table_name="email_outbox")
    op.drop_constraint(
        "ck_email_outbox_processing_started_state",
        "email_outbox",
        type_="check",
    )
    op.drop_column("email_outbox", "next_attempt_at")
    op.drop_column("email_outbox", "processing_started_at")
