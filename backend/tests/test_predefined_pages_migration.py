from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models.page import Page

EXPECTED_PAGES: tuple[tuple[str, str], ...] = (
    ("about", "О ложе"),
    ("lodges_spb", "Ложи Санкт-Петербурга"),
    ("principles", "Цели и принципы"),
    ("faq", "FAQ"),
    ("contacts", "Контакты"),
)
EXPECTED_KEYS = [key for key, _ in EXPECTED_PAGES]
EXPECTED_KEY_SET = {key for key, _ in EXPECTED_PAGES}
EXPECTED_CONTENT = "Материал ожидает утвержденного содержания."


def test_seed_definition_contains_exact_pages() -> None:
    migration = _load_migration()

    assert migration.revision == "20260824_0006"
    assert migration.down_revision == "20260823_0005"
    assert migration.MANAGED_PAGES == EXPECTED_PAGES


def test_upgrade_seeds_unpublished_pages_and_preserves_existing_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'pages.db'}")
    Base.metadata.create_all(engine, tables=[Page.__table__])

    with Session(bind=engine) as session:
        session.add(Page(key="about", title="Custom About", content="Custom content", is_published=True))
        session.commit()

    migration = _load_migration()

    with engine.begin() as connection:
        monkeypatch.setattr(migration.op, "execute", connection.execute)
        migration.upgrade()
        migration.upgrade()

    with Session(bind=engine) as session:
        pages = session.execute(select(Page).order_by(Page.key)).scalars().all()

    assert len(pages) == len(EXPECTED_PAGES)
    assert {page.key for page in pages} == EXPECTED_KEY_SET
    seeded_pages = {page.key: page for page in pages}
    assert seeded_pages["about"].title == "Custom About"
    assert seeded_pages["about"].content == "Custom content"
    assert seeded_pages["about"].is_published is True

    for key, title in EXPECTED_PAGES[1:]:
        assert seeded_pages[key].title == title
        assert seeded_pages[key].content == EXPECTED_CONTENT
        assert seeded_pages[key].is_published is False

    migration.downgrade()

    with Session(bind=engine) as session:
        after_downgrade = session.execute(select(Page).order_by(Page.key)).scalars().all()

    assert len(after_downgrade) == len(EXPECTED_PAGES)
    assert {page.key for page in after_downgrade} == EXPECTED_KEY_SET
    downgraded_pages = {page.key: page for page in after_downgrade}
    assert downgraded_pages["about"].title == "Custom About"
    assert downgraded_pages["about"].content == "Custom content"


def test_upgrade_from_empty_database_seeds_all_pages_unpublished(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'empty-pages.db'}")
    Base.metadata.create_all(engine, tables=[Page.__table__])

    migration = _load_migration()

    with engine.begin() as connection:
        monkeypatch.setattr(migration.op, "execute", connection.execute)
        migration.upgrade()

    with Session(bind=engine) as session:
        pages = session.execute(select(Page).order_by(Page.key)).scalars().all()

    assert len(pages) == len(EXPECTED_PAGES)
    assert {page.key for page in pages} == EXPECTED_KEY_SET
    assert all(page.is_published is False for page in pages)
    seeded_pages = {page.key: page for page in pages}
    for key, title in EXPECTED_PAGES:
        assert seeded_pages[key].title == title
        assert seeded_pages[key].content == EXPECTED_CONTENT


def _load_migration() -> ModuleType:
    path = Path("alembic/versions/20260824_0006_predefined_pages.py")
    spec = spec_from_file_location("predefined_pages_migration", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load predefined pages migration")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
