"""Add skills.spec column

Revision ID: 3f9c2b0e1b6a
Revises: 8c1a9d4a4c2b
Create Date: 2026-02-07 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "3f9c2b0e1b6a"
down_revision: Union[str, None] = "8c1a9d4a4c2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "skills",
        sa.Column("spec", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("skills", "spec")

