from __future__ import annotations

from datetime import datetime
from typing import Annotated
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator

from app.services.identifiers import validate_news_slug
from app.services.video_urls import validate_video_url


def _required_text(value: str, *, max_length: int, trim: bool = False) -> str:
    if "\x00" in value or not value.strip():
        raise ValueError("Text must not be blank")
    value = value.strip() if trim else value
    if len(value) > max_length:
        raise ValueError("Text is too long")
    return value


def _image_url(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value or len(value) > 500 or any(ord(char) < 32 for char in value) or "\\" in value:
        raise ValueError("Invalid image URL")
    if value.startswith("//"):
        raise ValueError("Invalid image URL")
    parsed = urlparse(value)
    if value.startswith("/"):
        if parsed.scheme or parsed.netloc:
            raise ValueError("Invalid image URL")
        return value
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("Invalid image URL")
    return value


class _AdminSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AdminNewsCreate(_AdminSchema):
    slug: Annotated[str, Field(max_length=160)]
    title: Annotated[str, Field(max_length=255)]
    excerpt: str
    body: str
    image_url: str | None = None
    is_published: StrictBool = False

    @field_validator("slug")
    @classmethod
    def valid_slug(cls, value: str) -> str:
        return validate_news_slug(value.strip())

    @field_validator("title")
    @classmethod
    def valid_title(cls, value: str) -> str:
        return _required_text(value, max_length=255, trim=True)

    @field_validator("excerpt")
    @classmethod
    def valid_excerpt(cls, value: str) -> str:
        return _required_text(value, max_length=10_000)

    @field_validator("body")
    @classmethod
    def valid_body(cls, value: str) -> str:
        return _required_text(value, max_length=1_000_000)

    @field_validator("image_url")
    @classmethod
    def valid_image_url(cls, value: str | None) -> str | None:
        return _image_url(value)


class AdminNewsPatch(_AdminSchema):
    slug: Annotated[str | None, Field(max_length=160)] = None
    title: Annotated[str | None, Field(max_length=255)] = None
    excerpt: str | None = None
    body: str | None = None
    image_url: str | None = None
    is_published: StrictBool | None = None

    @field_validator("slug")
    @classmethod
    def valid_slug(cls, value: str | None) -> str | None:
        return None if value is None else validate_news_slug(value.strip())

    @field_validator("title")
    @classmethod
    def valid_title(cls, value: str | None) -> str | None:
        return None if value is None else _required_text(value, max_length=255, trim=True)

    @field_validator("excerpt")
    @classmethod
    def valid_excerpt(cls, value: str | None) -> str | None:
        return None if value is None else _required_text(value, max_length=10_000)

    @field_validator("body")
    @classmethod
    def valid_body(cls, value: str | None) -> str | None:
        return None if value is None else _required_text(value, max_length=1_000_000)

    @field_validator("image_url")
    @classmethod
    def valid_image_url(cls, value: str | None) -> str | None:
        return _image_url(value)


class AdminVideoCreate(_AdminSchema):
    title: Annotated[str, Field(max_length=255)]
    description: str
    source_url: Annotated[str, Field(max_length=500)]
    is_published: StrictBool = False

    @field_validator("title")
    @classmethod
    def valid_title(cls, value: str) -> str:
        return _required_text(value, max_length=255, trim=True)

    @field_validator("description")
    @classmethod
    def valid_description(cls, value: str) -> str:
        return _required_text(value, max_length=1_000_000)

    @field_validator("source_url")
    @classmethod
    def valid_source_url(cls, value: str) -> str:
        return validate_video_url(value.strip()).source_url


class AdminVideoPatch(_AdminSchema):
    title: Annotated[str | None, Field(max_length=255)] = None
    description: str | None = None
    source_url: Annotated[str | None, Field(max_length=500)] = None
    is_published: StrictBool | None = None

    @field_validator("title")
    @classmethod
    def valid_title(cls, value: str | None) -> str | None:
        return None if value is None else _required_text(value, max_length=255, trim=True)

    @field_validator("description")
    @classmethod
    def valid_description(cls, value: str | None) -> str | None:
        return None if value is None else _required_text(value, max_length=1_000_000)

    @field_validator("source_url")
    @classmethod
    def valid_source_url(cls, value: str | None) -> str | None:
        return None if value is None else validate_video_url(value.strip()).source_url


class AdminPagePatch(_AdminSchema):
    title: Annotated[str | None, Field(max_length=255)] = None
    content: str | None = None
    is_published: StrictBool | None = None

    @field_validator("title")
    @classmethod
    def valid_title(cls, value: str | None) -> str | None:
        return None if value is None else _required_text(value, max_length=255, trim=True)

    @field_validator("content")
    @classmethod
    def valid_content(cls, value: str | None) -> str | None:
        return None if value is None else _required_text(value, max_length=1_000_000)


class AdminNewsListItem(_AdminSchema):
    id: int
    slug: str
    title: str
    excerpt: str
    image_url: str | None
    is_published: bool
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AdminNewsDetail(AdminNewsListItem):
    body: str


class AdminVideoListItem(_AdminSchema):
    id: int
    title: str
    description: str
    source_url: str
    provider: str
    is_published: bool
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AdminVideoDetail(AdminVideoListItem):
    embed_url: str


class AdminPageListItem(_AdminSchema):
    key: str
    title: str
    is_published: bool
    updated_at: datetime


class AdminPageDetail(_AdminSchema):
    key: str
    title: str
    content: str
    is_published: bool
    created_at: datetime
    updated_at: datetime


class AdminNewsListResponse(_AdminSchema):
    items: list[AdminNewsListItem]
    limit: int
    offset: int


class AdminVideoListResponse(_AdminSchema):
    items: list[AdminVideoListItem]
    limit: int
    offset: int


class AdminPageListResponse(_AdminSchema):
    items: list[AdminPageListItem]
    limit: int
    offset: int
