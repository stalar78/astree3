from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError

from app.models.news import NewsPost
from app.models.video import Video

PUBLISHED_UNIQUE_ERROR = "News slug already exists"


def apply_publication_state(
    entity: NewsPost | Video,
    requested_state: bool,
    *,
    is_new: bool = False,
) -> None:
    if requested_state and (is_new or entity.published_at is None):
        entity.published_at = datetime.now(UTC)
    entity.is_published = requested_state


def is_news_slug_conflict(error: IntegrityError) -> bool:
    message = str(error.orig or error).lower()
    return "news_posts" in message and "slug" in message


def is_blank(value: str) -> bool:
    return not value.strip()


__all__ = [
    "PUBLISHED_UNIQUE_ERROR",
    "apply_publication_state",
    "is_blank",
    "is_news_slug_conflict",
]
