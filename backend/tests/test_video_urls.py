import pytest

from app.models.video import Video
from app.services.video_urls import VideoUrlValidationError, validate_video_url


def test_valid_rutube_url_accepted_and_embed_derived() -> None:
    validated = validate_video_url("https://rutube.ru/video/0123456789abcdef0123456789abcdef/")

    assert validated.provider == "rutube"
    assert validated.embed_url == "https://rutube.ru/play/embed/0123456789abcdef0123456789abcdef/"


def test_malformed_rutube_url_rejected() -> None:
    with pytest.raises(VideoUrlValidationError):
        validate_video_url("https://rutube.ru/channel/123/")


def test_unsupported_provider_rejected() -> None:
    with pytest.raises(VideoUrlValidationError):
        validate_video_url("https://example.com/video/123")


def test_arbitrary_iframe_html_rejected() -> None:
    with pytest.raises(VideoUrlValidationError):
        validate_video_url('<iframe src="https://rutube.ru/play/embed/123/"></iframe>')


def test_video_model_does_not_store_embed_html() -> None:
    with pytest.raises(VideoUrlValidationError):
        Video(
            title="Bad",
            description="Bad",
            source_url='<iframe src="https://rutube.ru/play/embed/123/"></iframe>',
            provider="rutube",
            is_published=True,
        )
