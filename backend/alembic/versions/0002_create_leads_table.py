"""create leads table

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-11
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("whatsapp", sa.String(length=20), nullable=False),
        sa.Column("nome", sa.String(length=150), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="inbound_recebido"),
        sa.Column("primeira_mensagem", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_leads_whatsapp", "leads", ["whatsapp"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_leads_whatsapp", table_name="leads")
    op.drop_table("leads")
