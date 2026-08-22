import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.news import NewsPostListItem, NewsPostPublic
from app.schemas.page import PagePublic
from app.schemas.video import VideoPublic
from app.services import public_content

router = APIRouter(tags=["public-content"])
DbSession = Annotated[Session, Depends(get_db)]

SlugPath = Annotated[
    str,
    Path(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", min_length=1, max_length=160),
]
PageKeyPath = Annotated[
    str,
    Path(pattern=r"^[a-z0-9_]+$", min_length=1, max_length=80),
]
LimitQuery = Annotated[int, Query(ge=1, le=public_content.MAX_LIMIT)]
OffsetQuery = Annotated[int, Query(ge=0)]


@router.get("/pages/{key}", response_model=PagePublic)
def get_page(key: PageKeyPath, db: DbSession) -> PagePublic:
    page = public_content.get_published_page(db, key)
    if page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")
    return page


@router.get("/news", response_model=list[NewsPostListItem])
def list_news(
    db: DbSession,
    limit: LimitQuery = public_content.DEFAULT_LIMIT,
    offset: OffsetQuery = 0,
) -> list[NewsPostListItem]:
    return public_content.list_published_news(db, limit=limit, offset=offset)


@router.get("/news/{slug}", response_model=NewsPostPublic)
def get_news_post(slug: SlugPath, db: DbSession) -> NewsPostPublic:
    post = public_content.get_published_news_by_slug(db, slug)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News post not found")
    return post


@router.get("/videos", response_model=list[VideoPublic])
def list_videos(
    db: DbSession,
    limit: LimitQuery = public_content.DEFAULT_LIMIT,
    offset: OffsetQuery = 0,
) -> list[VideoPublic]:
    return public_content.list_published_videos(db, limit=limit, offset=offset)


@router.get("/videos/{video_id}", response_model=VideoPublic)
def get_video(video_id: int, db: DbSession) -> VideoPublic:
    video = public_content.get_published_video(db, video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return video


def is_valid_slug(value: str) -> bool:
    return re.fullmatch(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", value) is not None
