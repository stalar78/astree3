from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.db.base import Base
from app.models.mixins import TimestampMixin
from app.services.video_urls import (
    VideoUrlValidationError,
    derive_rutube_embed_url,
    validate_video_url,
)


class Video(TimestampMixin, Base):
    __tablename__ = "videos"
    __table_args__ = (
        Index("ix_videos_public_order", "is_published", "published_at", "id"),
        CheckConstraint("provider = 'rutube'", name="ck_videos_provider_rutube"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @validates("source_url")
    def validate_source_url(self, _: str, value: str) -> str:
        validated = validate_video_url(value)
        self.provider = validated.provider
        return validated.source_url

    @validates("provider")
    def validate_provider(self, _: str, value: str) -> str:
        if value != "rutube":
            raise VideoUrlValidationError("Unsupported video provider")
        return value

    @property
    def embed_url(self) -> str:
        if self.provider != "rutube":
            raise VideoUrlValidationError("Unsupported video provider")
        return derive_rutube_embed_url(self.source_url)
