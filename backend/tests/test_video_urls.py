import pytest

from app.models.video import Video
from app.services.video_urls import VideoUrlValidationError, validate_video_url


def test_valid_rutube_url_accepted_and_embed_derived() -> None:
    validated = validate_video_url("https://rutube.ru/video/0123456789ABCDEF0123456789abcdef/")

    assert validated.provider == "rutube"
    assert validated.source_url == "https://rutube.ru/video/0123456789abcdef0123456789abcdef/"
    assert validated.embed_url == "https://rutube.ru/play/embed/0123456789abcdef0123456789abcdef/"


def test_valid_rutube_embed_url_normalizes_to_public_source_url() -> None:
    validated = validate_video_url("https://rutube.ru/play/embed/0123456789abcdef0123456789abcdef/")

    assert validated.source_url == "https://rutube.ru/video/0123456789abcdef0123456789abcdef/"
    assert validated.embed_url == "https://rutube.ru/play/embed/0123456789abcdef0123456789abcdef/"


def test_http_rutube_url_rejected() -> None:
    with pytest.raises(VideoUrlValidationError):
        validate_video_url("http://rutube.ru/video/0123456789abcdef0123456789abcdef/")


def test_non_32_hex_video_id_rejected() -> None:
    with pytest.raises(VideoUrlValidationError):
        validate_video_url("https://rutube.ru/video/not-a-valid-id/")


def test_unrelated_rutube_path_with_video_id_query_rejected() -> None:
    with pytest.raises(VideoUrlValidationError):
        validate_video_url("https://rutube.ru/channel/123/?video_id=0123456789abcdef0123456789abcdef")


def test_url_with_userinfo_port_or_query_rejected() -> None:
    for value in [
        "https://user@rutube.ru/video/0123456789abcdef0123456789abcdef/",
        "https://rutube.ru:443/video/0123456789abcdef0123456789abcdef/",
        "https://rutube.ru/video/0123456789abcdef0123456789abcdef/?utm=test",
    ]:
        with pytest.raises(VideoUrlValidationError):
            validate_video_url(value)


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


def test_video_provider_is_derived_and_conflicting_assignment_rejected() -> None:
    video = Video(
        title="Good",
        description="Good",
        source_url="https://rutube.ru/video/0123456789abcdef0123456789abcdef/",
        provider="rutube",
        is_published=True,
    )

    assert video.source_url == "https://rutube.ru/video/0123456789abcdef0123456789abcdef/"
    assert video.provider == "rutube"

    with pytest.raises(VideoUrlValidationError):
        video.provider = "youtube"
