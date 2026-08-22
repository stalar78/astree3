from __future__ import annotations

import re
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.services.candidate_intake import (
    CandidateIntakeError,
    CandidateIntakePersistenceError,
    CandidateSubmissionData,
    intake_candidate_application,
)
from app.services.candidate_photos import (
    CandidatePhotoLimits,
    CandidatePhotoValidationError,
    prepare_candidate_photo,
)
from app.services.private_photo_storage import PrivatePhotoStorage

MAX_TEXT_FIELD_LENGTH = 4000
MAX_OPTIONAL_TEXT_FIELD_LENGTH = 4000
UPLOAD_CHUNK_SIZE = 64 * 1024

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_PATTERN = re.compile(r"^[0-9+\-().\s]{6,80}$")

router = APIRouter(tags=["candidate-intake"])


class CandidateAcceptedResponse(BaseModel):
    accepted: bool


class CandidateRateLimiter:
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
    "/candidate-applications",
    status_code=status.HTTP_201_CREATED,
    response_model=CandidateAcceptedResponse,
)
async def create_candidate_application(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
    full_name: Annotated[str, Form(...)],
    date_of_birth: Annotated[date, Form(...)],
    city: Annotated[str, Form(...)],
    phone: Annotated[str, Form(...)],
    email: Annotated[str, Form(...)],
    education: Annotated[str, Form(...)],
    occupation: Annotated[str, Form(...)],
    marital_status: Annotated[str, Form(...)],
    motivation: Annotated[str, Form(...)],
    photo: Annotated[UploadFile, File(...)],
    personal_data_processing: Annotated[str, Form(...)],
    privacy_policy_acknowledgement: Annotated[str, Form(...)],
    saint_petersburg_acknowledgement: Annotated[str, Form(...)],
    other_organizations: Annotated[str | None, Form()] = "",
    social_links: Annotated[str | None, Form()] = "",
    website: Annotated[str, Form()] = "",
) -> CandidateAcceptedResponse:
    _reject_honeypot(website)
    _reject_missing_consents(
        personal_data_processing,
        privacy_policy_acknowledgement,
        saint_petersburg_acknowledgement,
    )
    submission = CandidateSubmissionData(
        full_name=_clean_required_text(full_name, 255),
        date_of_birth=date_of_birth,
        city=_clean_required_text(city, 120),
        phone=_validate_phone(phone),
        email=_validate_email(email),
        education=_clean_required_text(education, MAX_TEXT_FIELD_LENGTH),
        occupation=_clean_required_text(occupation, MAX_TEXT_FIELD_LENGTH),
        marital_status=_clean_required_text(marital_status, 120),
        other_organizations=_clean_optional_text(other_organizations),
        social_links=_clean_optional_text(social_links),
        motivation=_clean_required_text(motivation, MAX_TEXT_FIELD_LENGTH),
    )
    _apply_rate_limit(request)

    try:
        photo_bytes = await _read_upload_file(photo, settings.candidate_photo_max_bytes)
        prepared_photo = prepare_candidate_photo(
            photo_bytes,
            CandidatePhotoLimits(
                max_bytes=settings.candidate_photo_max_bytes,
                max_pixels=settings.candidate_photo_max_pixels,
                max_edge=settings.candidate_photo_max_edge,
                output_max_edge=settings.candidate_photo_output_max_edge,
            ),
        )
    except CandidatePhotoValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid candidate photo") from exc
    finally:
        await photo.close()

    try:
        intake_candidate_application(
            db=db,
            storage=PrivatePhotoStorage(settings.private_media_root),
            submission=submission,
            prepared_photo=prepared_photo,
            consent_versions=settings.candidate_consent_versions,
        )
    except (CandidateIntakeError, CandidateIntakePersistenceError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Candidate application temporarily unavailable",
        ) from exc

    return CandidateAcceptedResponse(accepted=True)


def _apply_rate_limit(request: Request) -> None:
    limiter = request.app.state.candidate_rate_limiter
    client = request.client
    identity = client.host if client is not None else "unknown"
    if not limiter.allow(identity):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many candidate application requests",
            headers={"Retry-After": str(limiter.window_seconds)},
        )


def _reject_honeypot(website: str) -> None:
    if website.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid candidate application")


def _reject_missing_consents(
    personal_data_processing: str,
    privacy_policy_acknowledgement: str,
    saint_petersburg_acknowledgement: str,
) -> None:
    if not all(
        (
            _is_strict_true(personal_data_processing),
            _is_strict_true(privacy_policy_acknowledgement),
            _is_strict_true(saint_petersburg_acknowledgement),
        )
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid candidate application")


async def _read_upload_file(photo: UploadFile, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await photo.read(min(UPLOAD_CHUNK_SIZE, max_bytes - total + 1))
        if not chunk:
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > max_bytes:
            raise CandidatePhotoValidationError("Candidate photo exceeds the maximum byte size")
    data = b"".join(chunks)
    if not data:
        raise CandidatePhotoValidationError("Candidate photo is empty")
    return data


def _clean_required_text(value: str, max_length: int) -> str:
    cleaned = _clean_text(value, max_length)
    if not cleaned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid candidate application")
    return cleaned


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = _clean_text(value, MAX_OPTIONAL_TEXT_FIELD_LENGTH)
    return cleaned or None


def _clean_text(value: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid candidate application")
    cleaned = value.strip()
    if len(cleaned) > max_length or _contains_control_characters(cleaned):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid candidate application")
    return cleaned


def _validate_email(value: str) -> str:
    cleaned = _clean_required_text(value, 255)
    if not EMAIL_PATTERN.fullmatch(cleaned):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid candidate application")
    return cleaned


def _validate_phone(value: str) -> str:
    cleaned = _clean_required_text(value, 80)
    if not PHONE_PATTERN.fullmatch(cleaned) or not any(char.isdigit() for char in cleaned):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid candidate application")
    return cleaned


def _contains_control_characters(value: str) -> bool:
    return any((ord(char) < 32 and char not in {"\n", "\r", "\t"}) or ord(char) == 127 for char in value)


def _is_strict_true(value: str) -> bool:
    return value.strip().lower() == "true"
