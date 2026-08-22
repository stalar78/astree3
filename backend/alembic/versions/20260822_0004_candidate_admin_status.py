"""add candidate application status for admin review

Revision ID: 20260822_0004
Revises: 20260822_0003
Create Date: 2026-08-22
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260822_0004"
down_revision: str | None = "20260822_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "candidate_applications",
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="new",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_candidate_applications_status",
        "candidate_applications",
        "status IN ('new', 'in_review', 'contacted', 'closed', 'archived')",
    )
    op.create_index(
        "ix_candidate_applications_status",
        "candidate_applications",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_candidate_applications_status", table_name="candidate_applications")
    op.drop_constraint("ck_candidate_applications_status", "candidate_applications", type_="check")
    op.drop_column("candidate_applications", "status")
