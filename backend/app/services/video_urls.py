from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse


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
    if parsed.scheme not in {"https", "http"}:
        raise VideoUrlValidationError("Video URL must use http or https")

    host = parsed.netloc.lower().removeprefix("www.")

    if host != "rutube.ru":
        raise VideoUrlValidationError("Unsupported video provider")

    video_id = _extract_rutube_video_id(parsed.path, parsed.query)
    if not video_id:
        raise VideoUrlValidationError("Malformed RuTube video URL")

    normalized = parsed.geturl()
    return ValidatedVideoUrl(
        source_url=normalized,
        provider="rutube",
        embed_url=f"https://rutube.ru/play/embed/{video_id}/",
    )


def derive_rutube_embed_url(source_url: str) -> str:
    return validate_video_url(source_url).embed_url


def _extract_rutube_video_id(path: str, query: str) -> str | None:
    parts = [part for part in path.split("/") if part]
    if len(parts) >= 2 and parts[0] == "video":
        return parts[1]
    if len(parts) >= 3 and parts[0] == "play" and parts[1] == "embed":
        return parts[2]

    query_values = parse_qs(query)
    video_ids = query_values.get("video_id")
    if video_ids:
        return video_ids[0]
    return None
