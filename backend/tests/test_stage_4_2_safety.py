from pathlib import Path

from app.db.base import Base


def test_metadata_contains_only_stage_4_2_tables() -> None:
    assert set(Base.metadata.tables) == {"pages", "news_posts", "videos"}


def test_no_write_content_routes_exist() -> None:
    route_source = Path("app/api/public_content.py").read_text(encoding="utf-8")

    for decorator in ("@router.post", "@router.put", "@router.patch", "@router.delete"):
        assert decorator not in route_source


def test_no_candidate_admin_email_models_introduced() -> None:
    model_files = {path.stem for path in Path("app/models").glob("*.py")}

    assert "candidate" not in model_files
    assert "admin" not in model_files
    assert "email" not in model_files


def test_migration_creates_only_public_content_tables() -> None:
    migration = Path("alembic/versions/20260822_0001_public_content.py").read_text(encoding="utf-8")

    assert '"pages"' in migration
    assert '"news_posts"' in migration
    assert '"videos"' in migration
    assert "candidate" not in migration
    assert "admin" not in migration
    assert "email" not in migration
    assert "iframe" not in migration.lower()
