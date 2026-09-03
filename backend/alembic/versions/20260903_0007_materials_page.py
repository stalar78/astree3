"""seed materials managed page

Revision ID: 20260903_0007
Revises: 20260824_0006
Create Date: 2026-09-03
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260903_0007"
down_revision: str | None = "20260824_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PAGE_KEY = "materials"
PAGE_TITLE = "Материалы"
SEED_CONTENT = "Материал ожидает утвержденного содержания."

PAGES = sa.table(
    "pages",
    sa.column("key", sa.String(length=80)),
    sa.column("title", sa.String(length=255)),
    sa.column("content", sa.Text()),
    sa.column("is_published", sa.Boolean()),
)


def upgrade() -> None:
    op.execute(
        sa.insert(PAGES).from_select(
            ["key", "title", "content", "is_published"],
            sa.select(
                sa.literal(PAGE_KEY),
                sa.literal(PAGE_TITLE),
                sa.literal(SEED_CONTENT),
                sa.literal(False),
            ).where(
                ~sa.exists(
                    sa.select(1).select_from(PAGES).where(PAGES.c.key == PAGE_KEY),
                )
            ),
        )
    )


def downgrade() -> None:
    # Keep administrator-owned page content intact because the migration cannot
    # reliably distinguish the original seed from later edits.
    pass
