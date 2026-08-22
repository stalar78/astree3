from __future__ import annotations

from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import desc, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.api.admin_auth import AuthenticatedAdmin, get_authenticated_admin, require_admin_csrf
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.candidate import CandidateApplication
from app.services.candidate_contracts import normalize_candidate_status
from app.services.candidate_photos import NORMALIZED_MEDIA_TYPE
from app.services.private_photo_storage import PrivatePhotoStorage, PrivatePhotoStorageError

router = APIRouter(prefix="/admin/candidates", tags=["admin-candidates"])


class AdminCandidateConsentRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consent_type: str
    accepted_at: datetime
    document_version: str


class AdminCandidateListItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    full_name: str | None
    city: str | None
    email: str | None
    phone: str | None
    status: str
    has_photo: bool
    created_at: datetime
    updated_at: datetime


class AdminCandidateListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AdminCandidateListItem]
    limit: int
    offset: int


class AdminCandidateDetailResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    full_name: str | None
    date_of_birth: date | None
    city: str | None
    phone: str | None
    email: str | None
    education: str | None
    occupation: str | None
    marital_status: str | None
    other_organizations: str | None
    social_links: str | None
    motivation: str | None
    status: str
    has_photo: bool
    created_at: datetime
    updated_at: datetime
    consents: list[AdminCandidateConsentRead]


class AdminCandidateStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(max_length=32)


class AdminCandidateStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    status: str


@router.get("", response_model=AdminCandidateListResponse)
def list_admin_candidates(
    admin: Annotated[AuthenticatedAdmin, Depends(get_authenticated_admin)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    status: Annotated[str | None, Query(max_length=32)] = None,
) -> JSONResponse:
    normalized_status = _normalize_status_or_422(status)
    if isinstance(normalized_status, JSONResponse):
        return normalized_status

    statement = (
        select(CandidateApplication)
        .order_by(desc(CandidateApplication.created_at), desc(CandidateApplication.id))
        .offset(offset)
        .limit(limit)
    )
    if normalized_status is not None:
        statement = statement.where(CandidateApplication.status == normalized_status)

    try:
        applications = db.execute(statement).scalars().all()
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(
            http_status.HTTP_503_SERVICE_UNAVAILABLE,
            "Candidate administration temporarily unavailable",
        )

    payload = AdminCandidateListResponse(
        items=[_serialize_candidate_list_item(application) for application in applications],
        limit=limit,
        offset=offset,
    )
    return _json_response(payload)


@router.get("/{application_id}", response_model=AdminCandidateDetailResponse)
def get_admin_candidate(
    application_id: int,
    admin: Annotated[AuthenticatedAdmin, Depends(get_authenticated_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> JSONResponse:
    statement = (
        select(CandidateApplication)
        .options(selectinload(CandidateApplication.consents))
        .where(CandidateApplication.id == application_id)
    )

    try:
        application = db.execute(statement).scalar_one_or_none()
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(
            http_status.HTTP_503_SERVICE_UNAVAILABLE,
            "Candidate administration temporarily unavailable",
        )

    if application is None:
        return _error_response(http_status.HTTP_404_NOT_FOUND, "Candidate application not found")

    payload = _serialize_candidate_detail(application)
    return _json_response(payload)


@router.get("/{application_id}/photo")
def get_admin_candidate_photo(
    application_id: int,
    admin: Annotated[AuthenticatedAdmin, Depends(get_authenticated_admin)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Response:
    statement = select(CandidateApplication).where(CandidateApplication.id == application_id)

    try:
        application = db.execute(statement).scalar_one_or_none()
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(
            http_status.HTTP_503_SERVICE_UNAVAILABLE,
            "Candidate administration temporarily unavailable",
        )

    if application is None or not application.photo_storage_key:
        return _error_response(http_status.HTTP_404_NOT_FOUND, "Candidate application not found")
    if application.photo_media_type != NORMALIZED_MEDIA_TYPE:
        return _error_response(
            http_status.HTTP_503_SERVICE_UNAVAILABLE,
            "Candidate photo temporarily unavailable",
        )

    storage = PrivatePhotoStorage(settings.private_media_root)
    try:
        photo_bytes = storage.read(application.photo_storage_key)
    except PrivatePhotoStorageError:
        return _error_response(
            http_status.HTTP_503_SERVICE_UNAVAILABLE,
            "Candidate photo temporarily unavailable",
        )

    if application.photo_size_bytes is not None and len(photo_bytes) != application.photo_size_bytes:
        return _error_response(
            http_status.HTTP_503_SERVICE_UNAVAILABLE,
            "Candidate photo temporarily unavailable",
        )

    return Response(
        content=photo_bytes,
        media_type=NORMALIZED_MEDIA_TYPE,
        headers={**_private_cache_headers(), "X-Content-Type-Options": "nosniff"},
    )


@router.patch("/{application_id}/status", response_model=AdminCandidateStatusResponse)
def update_admin_candidate_status(
    application_id: int,
    payload: AdminCandidateStatusUpdateRequest,
    admin: Annotated[AuthenticatedAdmin, Depends(require_admin_csrf)],
    db: Annotated[Session, Depends(get_db)],
) -> JSONResponse:
    normalized_status = _normalize_status_or_422(payload.status)
    if isinstance(normalized_status, JSONResponse):
        return normalized_status

    statement = select(CandidateApplication).where(CandidateApplication.id == application_id)
    try:
        application = db.execute(statement).scalar_one_or_none()
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(
            http_status.HTTP_503_SERVICE_UNAVAILABLE,
            "Candidate administration temporarily unavailable",
        )

    if application is None:
        return _error_response(http_status.HTTP_404_NOT_FOUND, "Candidate application not found")

    try:
        application.status = normalized_status
        db.commit()
    except SQLAlchemyError:
        _rollback_safely(db)
        return _error_response(
            http_status.HTTP_503_SERVICE_UNAVAILABLE,
            "Candidate administration temporarily unavailable",
        )

    return _json_response(AdminCandidateStatusResponse(id=application.id, status=application.status))


def _serialize_candidate_list_item(application: CandidateApplication) -> AdminCandidateListItem:
    return AdminCandidateListItem(
        id=application.id,
        full_name=application.full_name,
        city=application.city,
        email=application.email,
        phone=application.phone,
        status=application.status,
        has_photo=bool(application.photo_storage_key),
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


def _serialize_candidate_detail(application: CandidateApplication) -> AdminCandidateDetailResponse:
    consents = sorted(application.consents, key=lambda consent: consent.id)
    return AdminCandidateDetailResponse(
        id=application.id,
        full_name=application.full_name,
        date_of_birth=application.date_of_birth,
        city=application.city,
        phone=application.phone,
        email=application.email,
        education=application.education,
        occupation=application.occupation,
        marital_status=application.marital_status,
        other_organizations=application.other_organizations,
        social_links=application.social_links,
        motivation=application.motivation,
        status=application.status,
        has_photo=bool(application.photo_storage_key),
        created_at=application.created_at,
        updated_at=application.updated_at,
        consents=[
            AdminCandidateConsentRead(
                consent_type=consent.consent_type,
                accepted_at=consent.accepted_at,
                document_version=consent.document_version,
            )
            for consent in consents
        ],
    )


def _normalize_status_or_422(candidate_status: str | None) -> str | JSONResponse | None:
    if candidate_status is None:
        return None
    try:
        return normalize_candidate_status(candidate_status)
    except (TypeError, ValueError):
        return _error_response(http_status.HTTP_422_UNPROCESSABLE_CONTENT, "Invalid candidate status")


def _json_response(payload: BaseModel, *, status_code: int = http_status.HTTP_200_OK) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(payload),
        headers=_private_cache_headers(),
    )


def _error_response(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail},
        headers=_private_cache_headers(),
    )


def _private_cache_headers() -> dict[str, str]:
    return {
        "Cache-Control": "private, no-store",
        "Pragma": "no-cache",
    }


def _rollback_safely(db: Session) -> None:
    try:
        db.rollback()
    except SQLAlchemyError:
        pass


__all__ = [
    "router",
]
