import re
from dataclasses import dataclass
from urllib.parse import urlparse

RUTUBE_VIDEO_ID_PATTERN = re.compile(r"^[0-9a-fA-F]{32}$")


class VideoUrlValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ValidatedVideoUrl:
    source_url: str
    provider: str
    embed_url: str


def validate_video_url(value: str) -> ValidatedVideoUrl:
    if "<iframe" in value.lower() or "<" in value or ">" in value:
        raise VideoUrlValidationError("Embed HTML is not accepted")

    parsed = urlparse(value)
    if parsed.scheme != "https":
        raise VideoUrlValidationError("Video URL must use https")
    if parsed.username or parsed.password or parsed.port is not None:
        raise VideoUrlValidationError("Video URL authority is not supported")
    if parsed.query or parsed.fragment or parsed.params:
        raise VideoUrlValidationError("Video URL must be canonical")

    host = parsed.netloc.lower().removeprefix("www.")

    if host != "rutube.ru":
        raise VideoUrlValidationError("Unsupported video provider")

    video_id = _extract_rutube_video_id(parsed.path)
    if not video_id:
        raise VideoUrlValidationError("Malformed RuTube video URL")

    normalized_id = video_id.lower()
    normalized = f"https://rutube.ru/video/{normalized_id}/"
    return ValidatedVideoUrl(
        source_url=normalized,
        provider="rutube",
        embed_url=f"https://rutube.ru/play/embed/{normalized_id}/",
    )


def derive_rutube_embed_url(source_url: str) -> str:
    return validate_video_url(source_url).embed_url


def _extract_rutube_video_id(path: str) -> str | None:
    parts = [part for part in path.split("/") if part]
    if len(parts) == 2 and parts[0] == "video" and RUTUBE_VIDEO_ID_PATTERN.fullmatch(parts[1]):
        return parts[1]
    if (
        len(parts) == 3
        and parts[0] == "play"
        and parts[1] == "embed"
        and RUTUBE_VIDEO_ID_PATTERN.fullmatch(parts[2])
    ):
        return parts[2]
    return None
