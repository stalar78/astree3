from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import asc, desc, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.admin_auth import AuthenticatedAdmin, get_authenticated_admin, require_admin_csrf
from app.db.session import get_db
from app.models.news import NewsPost
from app.models.page import Page
from app.models.video import Video
from app.schemas.admin_content import (
    AdminNewsCreate,
    AdminNewsDetail,
    AdminNewsListItem,
    AdminNewsListResponse,
    AdminNewsPatch,
    AdminPageDetail,
    AdminPageListItem,
    AdminPageListResponse,
    AdminPagePatch,
    AdminVideoCreate,
    AdminVideoDetail,
    AdminVideoListItem,
    AdminVideoListResponse,
    AdminVideoPatch,
)
from app.services.admin_content import apply_publication_state, is_news_slug_conflict
from app.services.identifiers import PAGE_KEY_PATTERN

router = APIRouter(prefix="/admin/content", tags=["admin-content"])
DbSession = Annotated[Session, Depends(get_db)]
AdminRead = Annotated[AuthenticatedAdmin, Depends(get_authenticated_admin)]
AdminWrite = Annotated[AuthenticatedAdmin, Depends(require_admin_csrf)]

MAX_LIMIT = 100
DEFAULT_LIMIT = 20
NewsIdPath = Annotated[int, Path(ge=1)]
VideoIdPath = Annotated[int, Path(ge=1)]
PageKeyPath = Annotated[str, Path(pattern=PAGE_KEY_PATTERN.pattern, min_length=1, max_length=80)]


@router.get("/news", response_model=AdminNewsListResponse)
def list_news(
    db: DbSession,
    admin: AdminRead,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
    published: bool | None = None,
) -> JSONResponse:
    statement = _ordered(select(NewsPost), NewsPost).limit(limit).offset(offset)
    if published is not None:
        statement = statement.where(NewsPost.is_published.is_(published))
    try:
        posts = db.execute(statement).scalars().all()
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(503, "Content administration temporarily unavailable")
    payload = AdminNewsListResponse(
        items=[_news_list_item(post) for post in posts],
        limit=limit,
        offset=offset,
    )
    return _json_response(payload)


@router.post("/news", response_model=AdminNewsDetail, status_code=status.HTTP_201_CREATED)
def create_news(payload: AdminNewsCreate, admin: AdminWrite, db: DbSession) -> JSONResponse:
    post = NewsPost(
        slug=payload.slug,
        title=payload.title,
        excerpt=payload.excerpt,
        body=payload.body,
        image_url=payload.image_url,
    )
    apply_publication_state(post, payload.is_published, is_new=True)
    db.add(post)
    error = _finalize_mutation(db, post, slug_conflict=True)
    if error is not None:
        return error
    return _json_response(_news_detail(post), status_code=201)


@router.get("/news/{news_id}", response_model=AdminNewsDetail)
def get_news(news_id: NewsIdPath, admin: AdminRead, db: DbSession) -> JSONResponse:
    try:
        post = db.execute(select(NewsPost).where(NewsPost.id == news_id)).scalar_one_or_none()
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(503, "Content administration temporarily unavailable")
    if post is None:
        return _error_response(404, "News post not found")
    return _json_response(_news_detail(post))


@router.patch("/news/{news_id}", response_model=AdminNewsDetail)
def update_news(
    news_id: NewsIdPath,
    payload: AdminNewsPatch,
    admin: AdminWrite,
    db: DbSession,
) -> JSONResponse:
    invalid = _reject_nulls(payload, {"slug", "title", "excerpt", "body", "is_published"})
    if invalid is not None:
        return invalid
    try:
        post = db.execute(select(NewsPost).where(NewsPost.id == news_id)).scalar_one_or_none()
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(503, "Content administration temporarily unavailable")
    if post is None:
        return _error_response(404, "News post not found")

    fields = payload.model_fields_set
    for field in ("slug", "title", "excerpt", "body", "image_url"):
        if field in fields:
            setattr(post, field, getattr(payload, field))
    if "is_published" in fields:
        apply_publication_state(post, payload.is_published)  # type: ignore[arg-type]
    error = _finalize_mutation(db, post, slug_conflict=True)
    if error is not None:
        return error
    return _json_response(_news_detail(post))


@router.delete("/news/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_news(news_id: NewsIdPath, admin: AdminWrite, db: DbSession) -> Response:
    try:
        post = db.execute(select(NewsPost).where(NewsPost.id == news_id)).scalar_one_or_none()
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(503, "Content administration temporarily unavailable")
    if post is None:
        return _error_response(404, "News post not found")
    db.delete(post)
    try:
        db.commit()
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(503, "Content administration temporarily unavailable")
    return Response(status_code=204, headers=_private_cache_headers())


@router.get("/videos", response_model=AdminVideoListResponse)
def list_videos(
    db: DbSession,
    admin: AdminRead,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
    published: bool | None = None,
) -> JSONResponse:
    statement = _ordered(select(Video), Video).limit(limit).offset(offset)
    if published is not None:
        statement = statement.where(Video.is_published.is_(published))
    try:
        videos = db.execute(statement).scalars().all()
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(503, "Content administration temporarily unavailable")
    return _json_response(
        AdminVideoListResponse(
            items=[_video_list_item(video) for video in videos],
            limit=limit,
            offset=offset,
        ),
    )


@router.post("/videos", response_model=AdminVideoDetail, status_code=status.HTTP_201_CREATED)
def create_video(payload: AdminVideoCreate, admin: AdminWrite, db: DbSession) -> JSONResponse:
    video = Video(
        title=payload.title,
        description=payload.description,
        source_url=payload.source_url,
        is_published=False,
    )
    apply_publication_state(video, payload.is_published, is_new=True)
    db.add(video)
    error = _finalize_mutation(db, video)
    if error is not None:
        return error
    return _json_response(_video_detail(video), status_code=201)


@router.get("/videos/{video_id}", response_model=AdminVideoDetail)
def get_video(video_id: VideoIdPath, admin: AdminRead, db: DbSession) -> JSONResponse:
    try:
        video = db.execute(select(Video).where(Video.id == video_id)).scalar_one_or_none()
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(503, "Content administration temporarily unavailable")
    if video is None:
        return _error_response(404, "Video not found")
    return _json_response(_video_detail(video))


@router.patch("/videos/{video_id}", response_model=AdminVideoDetail)
def update_video(
    video_id: VideoIdPath,
    payload: AdminVideoPatch,
    admin: AdminWrite,
    db: DbSession,
) -> JSONResponse:
    invalid = _reject_nulls(payload, {"title", "description", "source_url", "is_published"})
    if invalid is not None:
        return invalid
    try:
        video = db.execute(select(Video).where(Video.id == video_id)).scalar_one_or_none()
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(503, "Content administration temporarily unavailable")
    if video is None:
        return _error_response(404, "Video not found")
    fields = payload.model_fields_set
    for field in ("title", "description", "source_url"):
        if field in fields:
            setattr(video, field, getattr(payload, field))
    if "is_published" in fields:
        apply_publication_state(video, payload.is_published)  # type: ignore[arg-type]
    error = _finalize_mutation(db, video)
    if error is not None:
        return error
    return _json_response(_video_detail(video))


@router.delete("/videos/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(video_id: VideoIdPath, admin: AdminWrite, db: DbSession) -> Response:
    try:
        video = db.execute(select(Video).where(Video.id == video_id)).scalar_one_or_none()
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(503, "Content administration temporarily unavailable")
    if video is None:
        return _error_response(404, "Video not found")
    db.delete(video)
    try:
        db.commit()
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(503, "Content administration temporarily unavailable")
    return Response(status_code=204, headers=_private_cache_headers())


@router.get("/pages", response_model=AdminPageListResponse)
def list_pages(
    db: DbSession,
    admin: AdminRead,
) -> JSONResponse:
    statement = select(Page).order_by(asc(Page.key))
    try:
        pages = db.execute(statement).scalars().all()
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(503, "Content administration temporarily unavailable")
    return _json_response(
        AdminPageListResponse(
            items=[_page_list_item(page) for page in pages],
        ),
    )


@router.get("/pages/{key}", response_model=AdminPageDetail)
def get_page(key: PageKeyPath, admin: AdminRead, db: DbSession) -> JSONResponse:
    try:
        page = db.execute(select(Page).where(Page.key == key)).scalar_one_or_none()
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(503, "Content administration temporarily unavailable")
    if page is None:
        return _error_response(404, "Page not found")
    return _json_response(_page_detail(page))


@router.patch("/pages/{key}", response_model=AdminPageDetail)
def update_page(
    key: PageKeyPath,
    payload: AdminPagePatch,
    admin: AdminWrite,
    db: DbSession,
) -> JSONResponse:
    invalid = _reject_nulls(payload, {"title", "content", "is_published"})
    if invalid is not None:
        return invalid
    try:
        page = db.execute(select(Page).where(Page.key == key)).scalar_one_or_none()
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(503, "Content administration temporarily unavailable")
    if page is None:
        return _error_response(404, "Page not found")
    fields = payload.model_fields_set
    for field in ("title", "content", "is_published"):
        if field in fields:
            setattr(page, field, getattr(payload, field))
    error = _finalize_mutation(db, page)
    if error is not None:
        return error
    return _json_response(_page_detail(page))


def _ordered(statement, model):
    return statement.order_by(desc(model.updated_at), desc(model.id))


def _news_list_item(post: NewsPost) -> AdminNewsListItem:
    return AdminNewsListItem(
        id=post.id,
        slug=post.slug,
        title=post.title,
        excerpt=post.excerpt,
        image_url=post.image_url,
        is_published=post.is_published,
        published_at=post.published_at,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


def _news_detail(post: NewsPost) -> AdminNewsDetail:
    return AdminNewsDetail(body=post.body, **_news_list_item(post).model_dump())


def _video_list_item(video: Video) -> AdminVideoListItem:
    return AdminVideoListItem(
        id=video.id,
        title=video.title,
        description=video.description,
        source_url=video.source_url,
        provider=video.provider,
        is_published=video.is_published,
        published_at=video.published_at,
        created_at=video.created_at,
        updated_at=video.updated_at,
    )


def _video_detail(video: Video) -> AdminVideoDetail:
    return AdminVideoDetail(embed_url=video.embed_url, **_video_list_item(video).model_dump())


def _page_list_item(page: Page) -> AdminPageListItem:
    return AdminPageListItem(
        key=page.key,
        title=page.title,
        is_published=page.is_published,
        updated_at=page.updated_at,
    )


def _page_detail(page: Page) -> AdminPageDetail:
    return AdminPageDetail(
        key=page.key,
        title=page.title,
        content=page.content,
        is_published=page.is_published,
        created_at=page.created_at,
        updated_at=page.updated_at,
    )


def _json_response(payload, *, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(payload),
        headers=_private_cache_headers(),
    )


def _error_response(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail}, headers=_private_cache_headers())


def _private_cache_headers() -> dict[str, str]:
    return {"Cache-Control": "private, no-store", "Pragma": "no-cache"}


def _reject_nulls(payload, fields: set[str]) -> JSONResponse | None:
    for field in fields:
        if field in payload.model_fields_set and getattr(payload, field) is None:
            return _error_response(422, "Invalid admin content request")
    return None


def _finalize_mutation(db: Session, entity, *, slug_conflict: bool = False) -> JSONResponse | None:
    try:
        db.flush()
    except IntegrityError as exc:
        _rollback_safely(db)
        if slug_conflict and is_news_slug_conflict(exc):
            return _error_response(409, "News slug already exists")
        return _error_response(503, "Content administration temporarily unavailable")
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(503, "Content administration temporarily unavailable")

    try:
        db.refresh(entity)
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(503, "Content administration temporarily unavailable")

    try:
        db.commit()
    except IntegrityError as exc:
        _rollback_safely(db)
        if slug_conflict and is_news_slug_conflict(exc):
            return _error_response(409, "News slug already exists")
        return _error_response(503, "Content administration temporarily unavailable")
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(503, "Content administration temporarily unavailable")

    return None


def _rollback_safely(db: Session) -> None:
    try:
        db.rollback()
    except SQLAlchemyError:
        pass


__all__ = ["router"]
