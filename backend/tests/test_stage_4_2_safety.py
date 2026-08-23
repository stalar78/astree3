from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from sqlalchemy import CheckConstraint

from app.db.base import Base


def test_metadata_contains_only_stage_4_2_tables() -> None:
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


def test_no_write_content_routes_exist() -> None:
    route_source = Path("app/api/public_content.py").read_text(encoding="utf-8")

    for decorator in ("@router.post", "@router.put", "@router.patch", "@router.delete"):
        assert decorator not in route_source


def test_admin_models_are_present_and_standalone_email_models_are_not() -> None:
    model_files = {path.stem for path in Path("app/models").glob("*.py")}

    assert "admin" in model_files
    assert "email" not in model_files


def test_alembic_versions_stop_at_0005() -> None:
    versions = sorted(path.name for path in Path("alembic/versions").glob("*.py"))

    assert versions == [
        "20260822_0001_public_content.py",
        "20260822_0002_candidate_intake.py",
        "20260822_0003_admin_auth.py",
        "20260822_0004_candidate_admin_status.py",
        "20260823_0005_email_outbox_delivery_state.py",
    ]


def test_migration_creates_only_public_content_tables() -> None:
    migration = Path("alembic/versions/20260822_0001_public_content.py").read_text(encoding="utf-8")

    assert '"pages"' in migration
    assert '"news_posts"' in migration
    assert '"videos"' in migration
    assert "candidate" not in migration
    assert "admin" not in migration
    assert "email" not in migration
    assert "iframe" not in migration.lower()


def test_provider_constraint_is_only_on_videos_table(monkeypatch: pytest.MonkeyPatch) -> None:
    public_content_migration = _load_migration_module()
    created_tables: dict[str, tuple[Any, ...]] = {}

    def capture_create_table(name: str, *columns_and_constraints: Any, **_: Any) -> None:
        created_tables[name] = columns_and_constraints

    monkeypatch.setattr(public_content_migration.op, "create_table", capture_create_table)
    monkeypatch.setattr(public_content_migration.op, "create_index", _noop)
    monkeypatch.setattr(public_content_migration.op, "f", lambda name: name)

    public_content_migration.upgrade()

    page_constraints = _check_constraint_names(created_tables["pages"])
    video_constraints = _check_constraint_names(created_tables["videos"])

    assert "ck_videos_provider_rutube" not in page_constraints
    assert "ck_videos_provider_rutube" in video_constraints


def _check_constraint_names(columns_and_constraints: tuple[Any, ...]) -> set[str | None]:
    return {
        item.name
        for item in columns_and_constraints
        if isinstance(item, CheckConstraint)
    }


def _noop(*_: Any, **__: Any) -> None:
    return None


def _load_migration_module() -> ModuleType:
    path = Path("alembic/versions/20260822_0001_public_content.py")
    spec = spec_from_file_location("public_content_migration", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load public content migration")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
