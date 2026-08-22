import os
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from app.core.config import Settings
from app.db.base import Base
from app.services.candidate_photos import (
    NORMALIZED_MEDIA_TYPE,
    CandidatePhotoLimits,
    CandidatePhotoValidationError,
    prepare_candidate_photo,
)
from app.services.private_photo_storage import (
    PrivatePhotoStorage,
    PrivatePhotoStorageError,
    validate_candidate_photo_storage_key,
)


def test_jpeg_png_and_webp_are_normalized_to_jpeg() -> None:
    for image_format in ("JPEG", "PNG", "WEBP"):
        prepared = prepare_candidate_photo(_image_bytes(image_format), _limits())

        assert prepared.media_type == NORMALIZED_MEDIA_TYPE
        assert prepared.storage_key.startswith("candidate-photos/")
        assert prepared.storage_key.endswith(".jpg")
        with Image.open(BytesIO(prepared.normalized_bytes)) as output:
            assert output.format == "JPEG"
            assert output.mode == "RGB"
            assert output.size == (320, 240)


def test_large_valid_image_is_downscaled_preserving_aspect_ratio() -> None:
    prepared = prepare_candidate_photo(_image_bytes("JPEG", size=(400, 200)), _limits(output_max_edge=100))

    assert (prepared.width, prepared.height) == (100, 50)


def test_exif_orientation_is_applied_and_metadata_removed() -> None:
    raw = _oriented_jpeg_bytes()

    prepared = prepare_candidate_photo(raw, _limits())

    with Image.open(BytesIO(prepared.normalized_bytes)) as output:
        assert output.size == (40, 80)
        assert not output.getexif()
        assert "icc_profile" not in output.info


def test_transparent_png_flattens_to_rgb_jpeg() -> None:
    prepared = prepare_candidate_photo(_transparent_png_bytes(), _limits())

    with Image.open(BytesIO(prepared.normalized_bytes)) as output:
        assert output.format == "JPEG"
        assert output.mode == "RGB"


@pytest.mark.parametrize("payload", [b"not-an-image", b""])
def test_invalid_or_empty_bytes_rejected(payload: bytes) -> None:
    with pytest.raises(CandidatePhotoValidationError):
        prepare_candidate_photo(payload, _limits())


def test_gif_and_animated_image_rejected() -> None:
    with pytest.raises(CandidatePhotoValidationError):
        prepare_candidate_photo(_image_bytes("GIF"), _limits())

    with pytest.raises(CandidatePhotoValidationError):
        prepare_candidate_photo(_animated_webp_bytes(), _limits())


def test_oversized_byte_payload_rejected_before_decode() -> None:
    with pytest.raises(CandidatePhotoValidationError):
        prepare_candidate_photo(_image_bytes("JPEG"), _limits(max_bytes=10))


def test_dimensions_above_limits_rejected() -> None:
    with pytest.raises(CandidatePhotoValidationError):
        prepare_candidate_photo(_image_bytes("JPEG", size=(101, 50)), _limits(max_edge=100))

    with pytest.raises(CandidatePhotoValidationError):
        prepare_candidate_photo(_image_bytes("JPEG", size=(50, 50)), _limits(max_pixels=100))


def test_truncated_image_rejected() -> None:
    payload = _image_bytes("JPEG")[:20]

    with pytest.raises(CandidatePhotoValidationError):
        prepare_candidate_photo(payload, _limits())


def test_decompression_bomb_warning_becomes_domain_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 1)

    with pytest.raises(CandidatePhotoValidationError) as exc_info:
        prepare_candidate_photo(_image_bytes("JPEG", size=(2, 1)), _limits(max_pixels=100))

    assert str(exc_info.value) == "Candidate photo is not a valid supported image"


def test_decompression_bomb_error_becomes_domain_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_decompression_bomb_error(_: BytesIO):
        raise Image.DecompressionBombError("synthetic decompression bomb")

    monkeypatch.setattr(Image, "open", raise_decompression_bomb_error)

    with pytest.raises(CandidatePhotoValidationError) as exc_info:
        prepare_candidate_photo(b"synthetic-image-bytes", _limits())

    assert str(exc_info.value) == "Candidate photo is not a valid supported image"


def test_storage_saves_below_private_root_and_deletes(tmp_path: Path) -> None:
    storage = PrivatePhotoStorage(tmp_path)
    prepared = prepare_candidate_photo(_image_bytes("JPEG"), _limits())

    key = storage.save(prepared)
    path = storage.resolve_key(key)

    assert path.exists()
    assert tmp_path.resolve() in path.parents
    assert prepared.normalized_bytes == path.read_bytes()

    storage.delete(key)
    assert not path.exists()
    storage.delete(key)


def test_storage_reads_saved_photo(tmp_path: Path) -> None:
    storage = PrivatePhotoStorage(tmp_path)
    prepared = prepare_candidate_photo(_image_bytes("JPEG"), _limits())

    key = storage.save(prepared)

    assert storage.read(key) == prepared.normalized_bytes


def test_storage_read_rejects_missing_file(tmp_path: Path) -> None:
    storage = PrivatePhotoStorage(tmp_path)
    prepared = prepare_candidate_photo(_image_bytes("JPEG"), _limits())

    with pytest.raises(PrivatePhotoStorageError):
        storage.read(prepared.storage_key)


def test_storage_read_rejects_directory_target(tmp_path: Path) -> None:
    storage = PrivatePhotoStorage(tmp_path)
    prepared = prepare_candidate_photo(_image_bytes("JPEG"), _limits())
    path = storage.resolve_key(prepared.storage_key)
    path.mkdir(parents=True)

    with pytest.raises(PrivatePhotoStorageError):
        storage.read(prepared.storage_key)


def test_storage_read_rejects_final_symlink_when_supported(tmp_path: Path) -> None:
    if not hasattr(os, "symlink"):
        pytest.skip("symlink support is unavailable on this platform")

    storage = PrivatePhotoStorage(tmp_path)
    prepared = prepare_candidate_photo(_image_bytes("JPEG"), _limits())
    path = storage.resolve_key(prepared.storage_key)
    target = tmp_path / "symlink-target.jpg"
    target.write_bytes(prepared.normalized_bytes)

    try:
        path.symlink_to(target)
    except OSError:
        pytest.skip("symlink creation is unavailable on this platform")

    with pytest.raises(PrivatePhotoStorageError):
        storage.read(prepared.storage_key)


def test_storage_rejects_overwrite(tmp_path: Path) -> None:
    storage = PrivatePhotoStorage(tmp_path)
    prepared = prepare_candidate_photo(_image_bytes("JPEG"), _limits())

    storage.save(prepared)

    with pytest.raises(PrivatePhotoStorageError):
        storage.save(prepared)


@pytest.mark.parametrize(
    "key",
    [
        "../candidate-photos/00000000-0000-4000-8000-000000000000.jpg",
        "/candidate-photos/00000000-0000-4000-8000-000000000000.jpg",
        "C:\\candidate-photos\\00000000-0000-4000-8000-000000000000.jpg",
        "https://example.com/candidate-photos/00000000-0000-4000-8000-000000000000.jpg",
        "candidate-photos/00000000-0000-4000-8000-000000000000.png",
        "uploads/00000000-0000-4000-8000-000000000000.jpg",
    ],
)
def test_storage_key_validation_rejects_unsafe_keys(key: str) -> None:
    with pytest.raises(PrivatePhotoStorageError):
        validate_candidate_photo_storage_key(key)


def test_settings_have_safe_photo_defaults() -> None:
    settings = Settings(DATABASE_URL="postgresql://user:pass@localhost:5432/astrea")

    assert settings.private_media_root == Path("var/private")
    assert settings.candidate_photo_max_bytes == 10 * 1024 * 1024
    assert settings.candidate_photo_max_pixels == 20_000_000
    assert settings.candidate_photo_max_edge == 6000
    assert settings.candidate_photo_output_max_edge == 2048


def test_metadata_and_no_public_photo_api_or_static_mount() -> None:
    assert set(Base.metadata.tables) == {
        "pages",
        "news_posts",
        "videos",
        "candidate_applications",
        "application_consents",
        "email_outbox",
        "admin_users",
        "admin_sessions",
    }
    api_source = ""
    for path in Path("app/api").glob("*.py"):
        api_source += path.read_text(encoding="utf-8")
    assert "StaticFiles" not in api_source
    assert "candidate-photo" not in api_source
    assert "uploads" not in api_source


def test_prepared_photo_contains_no_original_filename_or_source_bytes() -> None:
    raw = _image_bytes("JPEG")
    prepared = prepare_candidate_photo(raw, _limits())

    assert not hasattr(prepared, "original_filename")
    assert not hasattr(prepared, "original_bytes")
    assert prepared.normalized_bytes != raw


def _limits(
    *,
    max_bytes: int = 10 * 1024 * 1024,
    max_pixels: int = 20_000_000,
    max_edge: int = 6000,
    output_max_edge: int = 2048,
) -> CandidatePhotoLimits:
    return CandidatePhotoLimits(
        max_bytes=max_bytes,
        max_pixels=max_pixels,
        max_edge=max_edge,
        output_max_edge=output_max_edge,
    )


def _image_bytes(image_format: str, size: tuple[int, int] = (320, 240)) -> bytes:
    mode = "RGB"
    image = Image.new(mode, size, (120, 80, 40))
    output = BytesIO()
    image.save(output, format=image_format)
    return output.getvalue()


def _transparent_png_bytes() -> bytes:
    image = Image.new("RGBA", (64, 64), (255, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 8, 56, 56), fill=(0, 128, 255, 128))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _oriented_jpeg_bytes() -> bytes:
    image = Image.new("RGB", (80, 40), (30, 60, 90))
    exif = Image.Exif()
    exif[274] = 6
    output = BytesIO()
    image.save(output, format="JPEG", exif=exif)
    return output.getvalue()


def _animated_webp_bytes() -> bytes:
    first = Image.new("RGB", (32, 32), (255, 0, 0))
    second = Image.new("RGB", (32, 32), (0, 255, 0))
    output = BytesIO()
    first.save(output, format="WEBP", save_all=True, append_images=[second], duration=100, loop=0)
    return output.getvalue()
