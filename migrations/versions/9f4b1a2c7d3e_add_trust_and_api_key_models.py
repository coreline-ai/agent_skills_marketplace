"""Add trust layer and developer API key models.

Revision ID: 9f4b1a2c7d3e
Revises: 5c9349039f96
Create Date: 2026-02-13 21:05:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "9f4b1a2c7d3e"
down_revision: Union[str, None] = "5c9349039f96"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def _has_table(table_name: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not _has_column("skills", "quality_score"):
        op.add_column("skills", sa.Column("quality_score", sa.Float(), nullable=True))
    if not _has_column("skills", "trust_score"):
        op.add_column("skills", sa.Column("trust_score", sa.Float(), nullable=True))
    if not _has_column("skills", "trust_level"):
        op.add_column("skills", sa.Column("trust_level", sa.String(), nullable=True))
    if not _has_column("skills", "trust_flags"):
        op.add_column(
            "skills",
            sa.Column("trust_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )
    if not _has_column("skills", "trust_last_verified_at"):
        op.add_column("skills", sa.Column("trust_last_verified_at", sa.DateTime(timezone=True), nullable=True))
    if not _has_column("skills", "trust_override"):
        op.add_column(
            "skills",
            sa.Column("trust_override", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )

    op.create_index(op.f("ix_skills_trust_score"), "skills", ["trust_score"], unique=False)
    op.create_index(op.f("ix_skills_trust_level"), "skills", ["trust_level"], unique=False)

    if not _has_table("skill_trust_audits"):
        op.create_table(
            "skill_trust_audits",
            sa.Column("skill_id", sa.UUID(), nullable=False),
            sa.Column("actor", sa.String(), nullable=False),
            sa.Column("action", sa.String(), nullable=False),
            sa.Column("reason", sa.String(), nullable=True),
            sa.Column("before", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("after", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["skill_id"], ["skills.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_skill_trust_audits_skill_id"),
            "skill_trust_audits",
            ["skill_id"],
            unique=False,
        )

    if not _has_table("api_keys"):
        op.create_table(
            "api_keys",
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("key_prefix", sa.String(), nullable=False),
            sa.Column("key_hash", sa.String(), nullable=False),
            sa.Column("scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("rate_limit_per_minute", sa.Integer(), nullable=False),
            sa.Column("created_by", sa.String(), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_api_keys_key_prefix"), "api_keys", ["key_prefix"], unique=False)
        op.create_index(op.f("ix_api_keys_key_hash"), "api_keys", ["key_hash"], unique=True)
        op.create_index(op.f("ix_api_keys_is_active"), "api_keys", ["is_active"], unique=False)

    if not _has_table("api_key_rate_windows"):
        op.create_table(
            "api_key_rate_windows",
            sa.Column("api_key_id", sa.UUID(), nullable=False),
            sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("request_count", sa.Integer(), nullable=False),
            sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["api_key_id"], ["api_keys.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("api_key_id", "window_start", name="uq_api_key_rate_windows_key_window"),
        )
        op.create_index(
            op.f("ix_api_key_rate_windows_api_key_id"),
            "api_key_rate_windows",
            ["api_key_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_api_key_rate_windows_window_start"),
            "api_key_rate_windows",
            ["window_start"],
            unique=False,
        )

    if not _has_table("api_key_usage_daily"):
        op.create_table(
            "api_key_usage_daily",
            sa.Column("api_key_id", sa.UUID(), nullable=False),
            sa.Column("usage_date", sa.Date(), nullable=False),
            sa.Column("request_count", sa.Integer(), nullable=False),
            sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["api_key_id"], ["api_keys.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("api_key_id", "usage_date", name="uq_api_key_daily_key_date"),
        )
        op.create_index(
            op.f("ix_api_key_usage_daily_api_key_id"),
            "api_key_usage_daily",
            ["api_key_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_api_key_usage_daily_usage_date"),
            "api_key_usage_daily",
            ["usage_date"],
            unique=False,
        )

    if not _has_table("api_key_usage_monthly"):
        op.create_table(
            "api_key_usage_monthly",
            sa.Column("api_key_id", sa.UUID(), nullable=False),
            sa.Column("usage_month", sa.Date(), nullable=False),
            sa.Column("request_count", sa.Integer(), nullable=False),
            sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["api_key_id"], ["api_keys.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("api_key_id", "usage_month", name="uq_api_key_monthly_key_month"),
        )
        op.create_index(
            op.f("ix_api_key_usage_monthly_api_key_id"),
            "api_key_usage_monthly",
            ["api_key_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_api_key_usage_monthly_usage_month"),
            "api_key_usage_monthly",
            ["usage_month"],
            unique=False,
        )


def downgrade() -> None:
    if _has_table("api_key_usage_monthly"):
        op.drop_index(op.f("ix_api_key_usage_monthly_usage_month"), table_name="api_key_usage_monthly")
        op.drop_index(op.f("ix_api_key_usage_monthly_api_key_id"), table_name="api_key_usage_monthly")
        op.drop_table("api_key_usage_monthly")

    if _has_table("api_key_usage_daily"):
        op.drop_index(op.f("ix_api_key_usage_daily_usage_date"), table_name="api_key_usage_daily")
        op.drop_index(op.f("ix_api_key_usage_daily_api_key_id"), table_name="api_key_usage_daily")
        op.drop_table("api_key_usage_daily")

    if _has_table("api_key_rate_windows"):
        op.drop_index(op.f("ix_api_key_rate_windows_window_start"), table_name="api_key_rate_windows")
        op.drop_index(op.f("ix_api_key_rate_windows_api_key_id"), table_name="api_key_rate_windows")
        op.drop_table("api_key_rate_windows")

    if _has_table("api_keys"):
        op.drop_index(op.f("ix_api_keys_is_active"), table_name="api_keys")
        op.drop_index(op.f("ix_api_keys_key_hash"), table_name="api_keys")
        op.drop_index(op.f("ix_api_keys_key_prefix"), table_name="api_keys")
        op.drop_table("api_keys")

    if _has_table("skill_trust_audits"):
        op.drop_index(op.f("ix_skill_trust_audits_skill_id"), table_name="skill_trust_audits")
        op.drop_table("skill_trust_audits")

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    index_names = {idx["name"] for idx in inspector.get_indexes("skills")}
    if op.f("ix_skills_trust_score") in index_names:
        op.drop_index(op.f("ix_skills_trust_score"), table_name="skills")
    if op.f("ix_skills_trust_level") in index_names:
        op.drop_index(op.f("ix_skills_trust_level"), table_name="skills")

    if _has_column("skills", "trust_override"):
        op.drop_column("skills", "trust_override")
    if _has_column("skills", "trust_last_verified_at"):
        op.drop_column("skills", "trust_last_verified_at")
    if _has_column("skills", "trust_flags"):
        op.drop_column("skills", "trust_flags")
    if _has_column("skills", "trust_level"):
        op.drop_column("skills", "trust_level")
    if _has_column("skills", "trust_score"):
        op.drop_column("skills", "trust_score")
    if _has_column("skills", "quality_score"):
        op.drop_column("skills", "quality_score")
