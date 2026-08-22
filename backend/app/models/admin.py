from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base
from app.models.mixins import TimestampMixin
from app.services.admin_auth import normalize_admin_username


class AdminUser(TimestampMixin, Base):
    __tablename__ = "admin_users"
    __table_args__ = (
        CheckConstraint(
            "length(username) >= 3 AND length(username) <= 80",
            name="ck_admin_users_username_length",
        ),
        CheckConstraint(
            "length(trim(password_hash)) > 0",
            name="ck_admin_users_password_hash_nonblank",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true(), nullable=False)

    sessions: Mapped[list[AdminSession]] = relationship(
        back_populates="admin_user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @validates("username")
    def validate_username(self, _: str, value: str) -> str:
        return normalize_admin_username(value)


class AdminSession(Base):
    __tablename__ = "admin_sessions"
    __table_args__ = (
        CheckConstraint(
            "length(token_hash) = 64",
            name="ck_admin_sessions_token_hash_length",
        ),
        CheckConstraint(
            "length(csrf_token_hash) = 64",
            name="ck_admin_sessions_csrf_token_hash_length",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_user_id: Mapped[int] = mapped_column(
        ForeignKey("admin_users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    csrf_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    admin_user: Mapped[AdminUser] = relationship(back_populates="sessions")
