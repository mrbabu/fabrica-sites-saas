"""create hunter_buscas and hunter_leads tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-22
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "hunter_buscas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nicho", sa.String(length=150), nullable=False),
        sa.Column("cidade", sa.String(length=150), nullable=False),
        sa.Column("bairro", sa.String(length=150), nullable=True),
        sa.Column("raio_km", sa.Integer(), nullable=True),
        sa.Column("quantidade_solicitada", sa.Integer(), nullable=False),
        sa.Column("quantidade_encontrada", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("origem", sa.String(length=30), nullable=False, server_default="hunter_web"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "hunter_leads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("busca_id", sa.Integer(), sa.ForeignKey("hunter_buscas.id"), nullable=True),
        sa.Column("place_id", sa.String(length=150), nullable=True),
        sa.Column("nome_empresa", sa.String(length=200), nullable=False),
        sa.Column("nicho", sa.String(length=150), nullable=False),
        sa.Column("cidade", sa.String(length=150), nullable=False),
        sa.Column("bairro", sa.String(length=150), nullable=True),
        sa.Column("telefone", sa.String(length=30), nullable=True),
        sa.Column("google_maps_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pendente"),
        sa.Column("slug_demo", sa.String(length=150), nullable=True),
        sa.Column("origem", sa.String(length=30), nullable=False, server_default="google_places"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_hunter_leads_place_id", "hunter_leads", ["place_id"], unique=False)
    op.create_index("ix_hunter_leads_nome_cidade", "hunter_leads", ["nome_empresa", "cidade"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_hunter_leads_nome_cidade", table_name="hunter_leads")
    op.drop_index("ix_hunter_leads_place_id", table_name="hunter_leads")
    op.drop_table("hunter_leads")
    op.drop_table("hunter_buscas")
