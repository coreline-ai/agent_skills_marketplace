"""Fix skills.trust_last_verified_at timezone type.

Revision ID: b7d9a9e6c4f2
Revises: 9f4b1a2c7d3e
Create Date: 2026-02-13 23:20:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7d9a9e6c4f2"
down_revision: Union[str, None] = "9f4b1a2c7d3e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def _is_timezone_aware(table_name: str, column_name: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    for col in inspector.get_columns(table_name):
        if col["name"] != column_name:
            continue
        return bool(getattr(col.get("type"), "timezone", False))
    return False


def upgrade() -> None:
    if not _has_column("skills", "trust_last_verified_at"):
        op.add_column("skills", sa.Column("trust_last_verified_at", sa.DateTime(timezone=True), nullable=True))
        return

    if not _is_timezone_aware("skills", "trust_last_verified_at"):
        op.alter_column(
            "skills",
            "trust_last_verified_at",
            existing_type=sa.DateTime(timezone=False),
            type_=sa.DateTime(timezone=True),
            existing_nullable=True,
            postgresql_using="trust_last_verified_at AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    if _has_column("skills", "trust_last_verified_at") and _is_timezone_aware("skills", "trust_last_verified_at"):
        op.alter_column(
            "skills",
            "trust_last_verified_at",
            existing_type=sa.DateTime(timezone=True),
            type_=sa.DateTime(timezone=False),
            existing_nullable=True,
            postgresql_using="trust_last_verified_at AT TIME ZONE 'UTC'",
        )
