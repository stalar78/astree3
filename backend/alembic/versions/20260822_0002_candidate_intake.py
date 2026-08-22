"""create candidate intake persistence contracts

Revision ID: 20260822_0002
Revises: 20260822_0001
Create Date: 2026-08-22
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260822_0002"
down_revision: str | None = "20260822_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "candidate_applications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("phone", sa.String(length=80), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("education", sa.Text(), nullable=True),
        sa.Column("occupation", sa.Text(), nullable=True),
        sa.Column("marital_status", sa.String(length=120), nullable=True),
        sa.Column("other_organizations", sa.Text(), nullable=True),
        sa.Column("social_links", sa.Text(), nullable=True),
        sa.Column("motivation", sa.Text(), nullable=True),
        sa.Column("photo_storage_key", sa.String(length=255), nullable=True),
        sa.Column("photo_media_type", sa.String(length=100), nullable=True),
        sa.Column("photo_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "application_consents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("consent_type", sa.String(length=80), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("document_version", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "consent_type IN ("
            "'personal_data_processing', "
            "'privacy_policy_acknowledgement', "
            "'saint_petersburg_acknowledgement'"
            ")",
            name="ck_application_consents_type",
        ),
        sa.CheckConstraint("length(document_version) > 0", name="ck_application_consents_document_version"),
        sa.ForeignKeyConstraint(["application_id"], ["candidate_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("application_id", "consent_type", name="uq_application_consents_type"),
    )
    op.create_index(op.f("ix_application_consents_application_id"), "application_consents", ["application_id"], unique=False)

    op.create_table(
        "email_outbox",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=80), server_default="candidate_application_received", nullable=False),
        sa.Column("status", sa.String(length=40), server_default="pending", nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "event_type IN ('candidate_application_received')",
            name="ck_email_outbox_event_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'sent', 'failed')",
            name="ck_email_outbox_status",
        ),
        sa.CheckConstraint("attempts >= 0", name="ck_email_outbox_attempts_non_negative"),
        sa.ForeignKeyConstraint(["application_id"], ["candidate_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_email_outbox_application_id"), "email_outbox", ["application_id"], unique=False)
    op.create_index("ix_email_outbox_status_created_at", "email_outbox", ["status", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_email_outbox_status_created_at", table_name="email_outbox")
    op.drop_index(op.f("ix_email_outbox_application_id"), table_name="email_outbox")
    op.drop_table("email_outbox")
    op.drop_index(op.f("ix_application_consents_application_id"), table_name="application_consents")
    op.drop_table("application_consents")
    op.drop_table("candidate_applications")
