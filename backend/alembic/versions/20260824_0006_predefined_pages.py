"""seed predefined managed pages

Revision ID: 20260824_0006
Revises: 20260823_0005
Create Date: 2026-08-24
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260824_0006"
down_revision: str | None = "20260823_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MANAGED_PAGES: tuple[tuple[str, str], ...] = (
    ("about", "О ложе"),
    ("lodges_spb", "Ложи Санкт-Петербурга"),
    ("principles", "Цели и принципы"),
    ("faq", "FAQ"),
    ("contacts", "Контакты"),
)
SEED_CONTENT = "Материал ожидает утвержденного содержания."

PAGES = sa.table(
    "pages",
    sa.column("key", sa.String(length=80)),
    sa.column("title", sa.String(length=255)),
    sa.column("content", sa.Text()),
    sa.column("is_published", sa.Boolean()),
)


def upgrade() -> None:
    for key, title in MANAGED_PAGES:
        op.execute(_insert_page_statement(key, title))


def downgrade() -> None:
    # Keep administrator-owned page content intact because the migration cannot
    # reliably distinguish seeded rows from later edits.
    pass


def _insert_page_statement(key: str, title: str):
    return sa.insert(PAGES).from_select(
        ["key", "title", "content", "is_published"],
        sa.select(
            sa.literal(key),
            sa.literal(title),
            sa.literal(SEED_CONTENT),
            sa.literal(False),
        ).where(
            ~sa.exists(
                sa.select(1).select_from(PAGES).where(PAGES.c.key == key),
            )
        ),
    )
