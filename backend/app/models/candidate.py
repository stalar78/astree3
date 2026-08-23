from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin
from app.services.candidate_contracts import (
    CANDIDATE_STATUS_NEW,
    CANDIDATE_STATUSES,
    CONSENT_TYPES,
    EMAIL_OUTBOX_EVENT_TYPES,
    EMAIL_OUTBOX_STATUSES,
)


def _sql_values(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


class CandidateApplication(TimestampMixin, Base):
    __tablename__ = "candidate_applications"
    __table_args__ = (
        CheckConstraint(
            "photo_size_bytes IS NULL OR photo_size_bytes >= 0",
            name="ck_candidate_applications_photo_size_non_negative",
        ),
        CheckConstraint(
            f"status IN ({_sql_values(CANDIDATE_STATUSES)})",
            name="ck_candidate_applications_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    education: Mapped[str | None] = mapped_column(Text, nullable=True)
    occupation: Mapped[str | None] = mapped_column(Text, nullable=True)
    marital_status: Mapped[str | None] = mapped_column(String(120), nullable=True)
    other_organizations: Mapped[str | None] = mapped_column(Text, nullable=True)
    social_links: Mapped[str | None] = mapped_column(Text, nullable=True)
    motivation: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    photo_media_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    photo_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        default=CANDIDATE_STATUS_NEW,
        server_default=CANDIDATE_STATUS_NEW,
        index=True,
        nullable=False,
    )

    consents: Mapped[list["ApplicationConsent"]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    email_outbox_entries: Mapped[list["EmailOutbox"]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ApplicationConsent(Base):
    __tablename__ = "application_consents"
    __table_args__ = (
        UniqueConstraint("application_id", "consent_type", name="uq_application_consents_type"),
        CheckConstraint(
            f"consent_type IN ({_sql_values(CONSENT_TYPES)})",
            name="ck_application_consents_type",
        ),
        CheckConstraint(
            "length(btrim(document_version)) > 0",
            name="ck_application_consents_document_version",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    consent_type: Mapped[str] = mapped_column(String(80), nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    document_version: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    application: Mapped[CandidateApplication] = relationship(back_populates="consents")


class EmailOutbox(TimestampMixin, Base):
    __tablename__ = "email_outbox"
    __table_args__ = (
        Index("ix_email_outbox_status_next_attempt_id", "status", "next_attempt_at", "id"),
        CheckConstraint(
            f"event_type IN ({_sql_values(EMAIL_OUTBOX_EVENT_TYPES)})",
            name="ck_email_outbox_event_type",
        ),
        CheckConstraint(
            f"status IN ({_sql_values(EMAIL_OUTBOX_STATUSES)})",
            name="ck_email_outbox_status",
        ),
        CheckConstraint("attempts >= 0", name="ck_email_outbox_attempts_non_negative"),
        CheckConstraint(
            "(status = 'processing' AND processing_started_at IS NOT NULL) "
            "OR (status != 'processing' AND processing_started_at IS NULL)",
            name="ck_email_outbox_processing_started_state",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(80),
        default="candidate_application_received",
        server_default="candidate_application_received",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(40),
        default="pending",
        server_default="pending",
        nullable=False,
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    last_error: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    application: Mapped[CandidateApplication] = relationship(
        back_populates="email_outbox_entries",
    )
