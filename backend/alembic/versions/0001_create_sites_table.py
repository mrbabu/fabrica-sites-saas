"""create sites table

Revision ID: 0001
Revises:
Create Date: 2026-07-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=150), nullable=False),
        sa.Column("nome_empresa", sa.String(length=100), nullable=False),
        sa.Column("nicho", sa.String(length=100), nullable=False),
        sa.Column("config", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_sites_slug", "sites", ["slug"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_sites_slug", table_name="sites")
    op.drop_table("sites")
