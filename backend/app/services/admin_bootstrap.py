from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.admin import AdminUser
from app.services.admin_auth import (
    hash_admin_password,
    normalize_admin_username,
    validate_admin_password,
)


class AdminBootstrapError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class AdminBootstrapResult:
    created: bool
    admin_user_id: int
    username: str


def bootstrap_initial_admin(db: Session, settings: Settings) -> AdminBootstrapResult:
    if settings.admin_initial_username is None or settings.admin_initial_password is None:
        raise AdminBootstrapError("Admin bootstrap credentials are not configured")

    try:
        username = normalize_admin_username(settings.admin_initial_username)
        password = validate_admin_password(settings.admin_initial_password.get_secret_value())
    except (TypeError, ValueError) as exc:
        raise AdminBootstrapError("Admin bootstrap credentials are invalid") from exc

    try:
        existing_admin = db.execute(
            select(AdminUser.id, AdminUser.username).order_by(AdminUser.id).limit(1),
        ).first()
        if existing_admin is not None:
            return AdminBootstrapResult(
                created=False,
                admin_user_id=existing_admin.id,
                username=existing_admin.username,
            )

        admin_user = AdminUser(
            username=username,
            password_hash=hash_admin_password(password),
            is_active=True,
        )
        db.add(admin_user)
        db.flush()
        admin_user_id = admin_user.id
        db.commit()
    except SQLAlchemyError as exc:
        try:
            db.rollback()
        except SQLAlchemyError:
            pass
        raise AdminBootstrapError("Admin bootstrap failed") from exc

    return AdminBootstrapResult(
        created=True,
        admin_user_id=admin_user_id,
        username=username,
    )


__all__ = [
    "AdminBootstrapError",
    "AdminBootstrapResult",
    "bootstrap_initial_admin",
]
