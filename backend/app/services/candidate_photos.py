from dataclasses import dataclass
from io import BytesIO
from uuid import uuid4

from PIL import Image, ImageOps, ImageSequence, UnidentifiedImageError

ACCEPTED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
NORMALIZED_MEDIA_TYPE = "image/jpeg"
NORMALIZED_EXTENSION = ".jpg"
JPEG_QUALITY = 89


class CandidatePhotoValidationError(ValueError):
    pass


@dataclass(frozen=True)
class CandidatePhotoLimits:
    max_bytes: int
    max_pixels: int
    max_edge: int
    output_max_edge: int


@dataclass(frozen=True)
class PreparedCandidatePhoto:
    storage_key: str
    media_type: str
    size_bytes: int
    width: int
    height: int
    normalized_bytes: bytes


def prepare_candidate_photo(upload_bytes: bytes, limits: CandidatePhotoLimits) -> PreparedCandidatePhoto:
    _validate_limits(limits)
    if not upload_bytes:
        raise CandidatePhotoValidationError("Candidate photo is empty")
    if len(upload_bytes) > limits.max_bytes:
        raise CandidatePhotoValidationError("Candidate photo exceeds the maximum byte size")

    try:
        with Image.open(BytesIO(upload_bytes)) as image:
            _validate_image_object(image, limits)
        with Image.open(BytesIO(upload_bytes)) as image:
            normalized_bytes, width, height = _normalize_image(image, limits.output_max_edge)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise CandidatePhotoValidationError("Candidate photo is not a valid supported image") from exc

    return PreparedCandidatePhoto(
        storage_key=generate_candidate_photo_storage_key(),
        media_type=NORMALIZED_MEDIA_TYPE,
        size_bytes=len(normalized_bytes),
        width=width,
        height=height,
        normalized_bytes=normalized_bytes,
    )


def generate_candidate_photo_storage_key() -> str:
    return f"candidate-photos/{uuid4()}{NORMALIZED_EXTENSION}"


def _validate_limits(limits: CandidatePhotoLimits) -> None:
    for value in (
        limits.max_bytes,
        limits.max_pixels,
        limits.max_edge,
        limits.output_max_edge,
    ):
        if value <= 0:
            raise CandidatePhotoValidationError("Candidate photo limits must be positive")


def _validate_image_object(image: Image.Image, limits: CandidatePhotoLimits) -> None:
    if image.format not in ACCEPTED_IMAGE_FORMATS:
        raise CandidatePhotoValidationError("Unsupported candidate photo format")
    if getattr(image, "is_animated", False) or _frame_count(image) != 1:
        raise CandidatePhotoValidationError("Animated or multi-frame images are not supported")

    width, height = image.size
    if width <= 0 or height <= 0:
        raise CandidatePhotoValidationError("Candidate photo dimensions are invalid")
    if width * height > limits.max_pixels:
        raise CandidatePhotoValidationError("Candidate photo exceeds the maximum pixel count")
    if width > limits.max_edge or height > limits.max_edge:
        raise CandidatePhotoValidationError("Candidate photo exceeds the maximum edge length")

    image.verify()


def _normalize_image(image: Image.Image, output_max_edge: int) -> tuple[bytes, int, int]:
    normalized = ImageOps.exif_transpose(image)
    normalized.load()

    if normalized.mode in {"RGBA", "LA"} or (
        normalized.mode == "P" and "transparency" in normalized.info
    ):
        background = Image.new("RGB", normalized.size, (255, 255, 255))
        alpha_source = normalized.convert("RGBA")
        background.paste(alpha_source, mask=alpha_source.getchannel("A"))
        normalized = background
    else:
        normalized = normalized.convert("RGB")

    normalized.thumbnail(
        (output_max_edge, output_max_edge),
        Image.Resampling.LANCZOS,
    )
    output = BytesIO()
    normalized.save(output, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    data = output.getvalue()
    return data, normalized.width, normalized.height


def _frame_count(image: Image.Image) -> int:
    try:
        return sum(1 for _ in ImageSequence.Iterator(image))
    except Exception as exc:
        raise CandidatePhotoValidationError("Candidate photo frame structure is invalid") from exc
