from __future__ import annotations

import hashlib
import re
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from argon2.low_level import Type

PASSWORD_HASHER = PasswordHasher(type=Type.ID)
_ADMIN_USERNAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,79}$")


def normalize_admin_username(username: str) -> str:
    if not isinstance(username, str):
        raise TypeError("Invalid admin username")

    normalized = username.strip().lower()
    if len(normalized) < 3 or len(normalized) > 80:
        raise ValueError("Invalid admin username")
    if not normalized.isascii() or _ADMIN_USERNAME_PATTERN.fullmatch(normalized) is None:
        raise ValueError("Invalid admin username")
    return normalized


def validate_admin_password(password: str) -> str:
    if not isinstance(password, str):
        raise TypeError("Invalid admin password")
    if len(password) < 12 or len(password) > 256:
        raise ValueError("Invalid admin password")
    if any(ord(char) < 32 or ord(char) == 127 for char in password):
        raise ValueError("Invalid admin password")
    return password


def hash_admin_password(password: str) -> str:
    return PASSWORD_HASHER.hash(validate_admin_password(password))


def verify_admin_password(password_hash: str, password: str) -> bool:
    try:
        validated_password = validate_admin_password(password)
    except ValueError:
        return False

    try:
        return PASSWORD_HASHER.verify(password_hash, validated_password)
    except VerificationError:
        return False


def admin_password_needs_rehash(password_hash: str) -> bool:
    try:
        return PASSWORD_HASHER.check_needs_rehash(password_hash)
    except InvalidHashError:
        return True


def generate_admin_session_token() -> str:
    return secrets.token_urlsafe(32)


def generate_admin_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def hash_admin_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_admin_csrf_token(token: str) -> str:
    return hash_admin_token(token)


__all__ = [
    "PASSWORD_HASHER",
    "admin_password_needs_rehash",
    "generate_admin_csrf_token",
    "generate_admin_session_token",
    "hash_admin_csrf_token",
    "hash_admin_password",
    "hash_admin_token",
    "normalize_admin_username",
    "validate_admin_password",
    "verify_admin_password",
]
