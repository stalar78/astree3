from sqlalchemy import Select, desc, nulls_last, select
from sqlalchemy.orm import Session

from app.models.news import NewsPost
from app.models.page import Page
from app.models.video import Video

MAX_LIMIT = 100
DEFAULT_LIMIT = 20


def get_published_page(db: Session, key: str) -> Page | None:
    statement = select(Page).where(Page.key == key, Page.is_published.is_(True))
    return db.execute(statement).scalar_one_or_none()


def list_published_news(db: Session, limit: int = DEFAULT_LIMIT, offset: int = 0) -> list[NewsPost]:
    statement = _published_ordered(select(NewsPost), NewsPost).limit(limit).offset(offset)
    return list(db.execute(statement).scalars().all())


def get_published_news_by_slug(db: Session, slug: str) -> NewsPost | None:
    statement = select(NewsPost).where(NewsPost.slug == slug, NewsPost.is_published.is_(True))
    return db.execute(statement).scalar_one_or_none()


def list_published_videos(db: Session, limit: int = DEFAULT_LIMIT, offset: int = 0) -> list[Video]:
    statement = _published_ordered(select(Video), Video).limit(limit).offset(offset)
    return list(db.execute(statement).scalars().all())


def get_published_video(db: Session, video_id: int) -> Video | None:
    statement = select(Video).where(Video.id == video_id, Video.is_published.is_(True))
    return db.execute(statement).scalar_one_or_none()


def _published_ordered(statement: Select[tuple[object]], model: type[NewsPost] | type[Video]):
    return statement.where(model.is_published.is_(True)).order_by(
        nulls_last(desc(model.published_at)),
        desc(model.id),
    )
