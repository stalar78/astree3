import os
import re
import stat
from pathlib import Path

from app.services.candidate_photos import PreparedCandidatePhoto

CANDIDATE_PHOTO_KEY_PATTERN = re.compile(
    r"^candidate-photos/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jpg$"
)


class PrivatePhotoStorageError(ValueError):
    pass


class PrivatePhotoStorage:
    def __init__(self, root: Path | str):
        self.root = Path(root)

    def read(self, storage_key: str) -> bytes:
        path = self._read_path(storage_key)
        if not hasattr(os, "O_NOFOLLOW") and path.is_symlink():
            raise PrivatePhotoStorageError("Candidate photo could not be read")

        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW

        try:
            fd = os.open(path, flags)
        except OSError as exc:
            raise PrivatePhotoStorageError("Candidate photo could not be read") from exc

        try:
            with os.fdopen(fd, "rb") as source:
                if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                    raise PrivatePhotoStorageError("Candidate photo could not be read")
                return source.read()
        except PrivatePhotoStorageError:
            raise
        except OSError as exc:
            raise PrivatePhotoStorageError("Candidate photo could not be read") from exc

    def save(self, photo: PreparedCandidatePhoto) -> str:
        destination = self.resolve_key(photo.storage_key)
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        try:
            fd = os.open(destination, flags, 0o600)
            with os.fdopen(fd, "wb") as output:
                output.write(photo.normalized_bytes)
        except FileExistsError as exc:
            raise PrivatePhotoStorageError("Candidate photo storage key already exists") from exc
        except OSError as exc:
            if destination.exists():
                destination.unlink(missing_ok=True)
            raise PrivatePhotoStorageError("Candidate photo could not be stored") from exc
        return photo.storage_key

    def delete(self, storage_key: str) -> None:
        path = self.resolve_key(storage_key)
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise PrivatePhotoStorageError("Candidate photo could not be deleted") from exc

    def resolve_key(self, storage_key: str) -> Path:
        validate_candidate_photo_storage_key(storage_key)
        root = self.root.resolve()
        path = (root / storage_key).resolve()
        if path != root and root not in path.parents:
            raise PrivatePhotoStorageError("Candidate photo storage key is invalid")
        return path

    def _read_path(self, storage_key: str) -> Path:
        validate_candidate_photo_storage_key(storage_key)
        root = self.root.resolve()
        path = root / storage_key
        resolved_path = path.resolve()
        if resolved_path != root and root not in resolved_path.parents:
            raise PrivatePhotoStorageError("Candidate photo storage key is invalid")
        return path


def validate_candidate_photo_storage_key(storage_key: str) -> None:
    if "\\" in storage_key or "://" in storage_key:
        raise PrivatePhotoStorageError("Candidate photo storage key is invalid")
    candidate = Path(storage_key)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise PrivatePhotoStorageError("Candidate photo storage key is invalid")
    if CANDIDATE_PHOTO_KEY_PATTERN.fullmatch(storage_key) is None:
        raise PrivatePhotoStorageError("Candidate photo storage key is invalid")
