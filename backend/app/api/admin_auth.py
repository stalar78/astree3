from __future__ import annotations

import secrets
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.admin import AdminSession, AdminUser
from app.services.admin_auth import (
    CSRF_COOKIE_NAME,
    CSRF_COOKIE_PATH,
    CSRF_HEADER_NAME,
    DUMMY_PASSWORD_HASH,
    SESSION_COOKIE_NAME,
    SESSION_COOKIE_PATH,
    admin_password_needs_rehash,
    generate_admin_csrf_token,
    generate_admin_session_token,
    hash_admin_csrf_token,
    hash_admin_password,
    hash_admin_token,
    is_valid_admin_auth_token,
    normalize_admin_username,
    verify_admin_password,
)

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])

class AdminLoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=256)


class AdminAuthResponse(BaseModel):
    authenticated: bool
    username: str


@dataclass(frozen=True, slots=True)
class AuthenticatedAdmin:
    user: AdminUser
    session: AdminSession


class AdminLoginRateLimiter:
    """Application-level MVP control; no Redis or persistence."""

    def __init__(
        self,
        request_limit: int,
        window_seconds: int,
        *,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.request_limit = request_limit
        self.window_seconds = window_seconds
        self._monotonic = monotonic
        self._buckets: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, identity: str) -> bool:
        now = self._monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._buckets[identity]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            allowed = len(bucket) < self.request_limit
            if allowed:
                bucket.append(now)
            self._prune_empty_buckets(cutoff)
            return allowed

    def _prune_empty_buckets(self, cutoff: float) -> None:
        for identity, bucket in list(self._buckets.items()):
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if not bucket:
                self._buckets.pop(identity, None)


@router.post(
    "/login",
    response_model=AdminAuthResponse,
)
def login_admin(
    request: Request,
    payload: AdminLoginRequest,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> JSONResponse:
    limiter = request.app.state.admin_login_rate_limiter
    client_host = request.client.host if request.client is not None else "unknown"
    if not limiter.allow(client_host):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many admin login attempts",
            headers={"Retry-After": str(limiter.window_seconds)},
        )

    try:
        normalized_username = normalize_admin_username(payload.username)
    except (TypeError, ValueError):
        _consume_dummy_password_work(payload.password)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")

    try:
        admin_user = db.scalar(select(AdminUser).where(AdminUser.username == normalized_username))
    except SQLAlchemyError as exc:
        _rollback_safely(db)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication temporarily unavailable",
        ) from exc

    if admin_user is None or not admin_user.is_active:
        _consume_dummy_password_work(payload.password)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")

    if not verify_admin_password(admin_user.password_hash, payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")

    raw_session_token = generate_admin_session_token()
    raw_csrf_token = generate_admin_csrf_token()
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.admin_session_ttl_seconds)

    try:
        if admin_password_needs_rehash(admin_user.password_hash):
            admin_user.password_hash = hash_admin_password(payload.password)

        admin_session = AdminSession(
            admin_user_id=admin_user.id,
            token_hash=hash_admin_token(raw_session_token),
            csrf_token_hash=hash_admin_csrf_token(raw_csrf_token),
            expires_at=expires_at,
        )
        db.add(admin_session)
        db.flush()
        db.commit()
    except SQLAlchemyError as exc:
        _rollback_safely(db)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication temporarily unavailable",
        ) from exc

    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"authenticated": True, "username": admin_user.username},
        headers={"Cache-Control": "no-store"},
    )
    _set_auth_cookies(response, raw_session_token, raw_csrf_token, settings, expires_at)
    return response


@router.post("/logout")
def logout_admin(
    admin: Annotated[AuthenticatedAdmin, Depends(require_admin_csrf)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    try:
        db.delete(admin.session)
        db.commit()
    except SQLAlchemyError as exc:
        _rollback_safely(db)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin logout temporarily unavailable",
        ) from exc

    response = Response(status_code=status.HTTP_204_NO_CONTENT, headers={"Cache-Control": "no-store"})
    _clear_auth_cookies(response)
    return response


@router.get("/me", response_model=AdminAuthResponse)
def current_admin(admin: Annotated[AuthenticatedAdmin, Depends(get_authenticated_admin)]) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"authenticated": True, "username": admin.user.username},
        headers={"Cache-Control": "no-store"},
    )


def get_authenticated_admin(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> AuthenticatedAdmin:
    raw_session_token = request.cookies.get(SESSION_COOKIE_NAME)
    if not is_valid_admin_auth_token(raw_session_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin session")

    session_token_hash = hash_admin_token(raw_session_token)

    try:
        row = db.execute(
            select(AdminSession, AdminUser)
            .join(AdminUser, AdminUser.id == AdminSession.admin_user_id)
            .where(AdminSession.token_hash == session_token_hash),
        ).first()
    except SQLAlchemyError as exc:
        _rollback_safely(db)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication temporarily unavailable",
        ) from exc

    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin session")

    admin_session, admin_user = row
    if not _hashes_match(admin_session.token_hash, session_token_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin session")
    if admin_session.expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin session")
    if not admin_user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin session")

    return AuthenticatedAdmin(user=admin_user, session=admin_session)


def require_admin_csrf(
    request: Request,
    admin: Annotated[AuthenticatedAdmin, Depends(get_authenticated_admin)],
) -> AuthenticatedAdmin:
    header_token = request.headers.get(CSRF_HEADER_NAME)
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    if not is_valid_admin_auth_token(header_token) or not is_valid_admin_auth_token(cookie_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin CSRF token")
    if not _tokens_match(header_token, cookie_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin CSRF token")
    if not _hashes_match(admin.session.csrf_token_hash, hash_admin_csrf_token(header_token)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin CSRF token")
    return admin


def _consume_dummy_password_work(password: str) -> None:
    verify_admin_password(DUMMY_PASSWORD_HASH, password)


def _set_auth_cookies(
    response: Response,
    raw_session_token: str,
    raw_csrf_token: str,
    settings: Settings,
    expires_at: datetime,
) -> None:
    secure = not settings.debug
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=raw_session_token,
        max_age=settings.admin_session_ttl_seconds,
        expires=expires_at,
        httponly=True,
        secure=secure,
        samesite="strict",
        path=SESSION_COOKIE_PATH,
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=raw_csrf_token,
        max_age=settings.admin_session_ttl_seconds,
        expires=expires_at,
        httponly=False,
        secure=secure,
        samesite="strict",
        path=CSRF_COOKIE_PATH,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path=SESSION_COOKIE_PATH)
    response.delete_cookie(key=CSRF_COOKIE_NAME, path=CSRF_COOKIE_PATH)


def _rollback_safely(db: Session) -> None:
    try:
        db.rollback()
    except SQLAlchemyError:
        pass


def _tokens_match(left: str, right: str) -> bool:
    return secrets.compare_digest(left, right)


def _hashes_match(left: str, right: str) -> bool:
    return secrets.compare_digest(left, right)


__all__ = [
    "AdminAuthResponse",
    "AdminLoginRateLimiter",
    "AdminLoginRequest",
    "AuthenticatedAdmin",
    "current_admin",
    "get_authenticated_admin",
    "logout_admin",
    "require_admin_csrf",
    "router",
]
