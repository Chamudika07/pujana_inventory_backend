"""add suppliers and bill supplier link

Revision ID: 0e7a99a1f214
Revises: 0441ebda47d1
Create Date: 2026-04-06 13:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0e7a99a1f214"
down_revision: Union[str, Sequence[str], None] = "0441ebda47d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("supplier_name", sa.String(length=255), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("contact_person", sa.String(length=255), nullable=True),
        sa.Column("phone_number", sa.String(length=30), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("payable_balance", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_suppliers_supplier_name"), "suppliers", ["supplier_name"], unique=False)
    op.create_index(op.f("ix_suppliers_company_name"), "suppliers", ["company_name"], unique=False)
    op.create_index(op.f("ix_suppliers_phone_number"), "suppliers", ["phone_number"], unique=False)
    op.create_index(op.f("ix_suppliers_email"), "suppliers", ["email"], unique=False)

    op.add_column("bills", sa.Column("supplier_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_bills_supplier_id"), "bills", ["supplier_id"], unique=False)
    op.create_foreign_key(
        "fk_bills_supplier_id_suppliers",
        "bills",
        "suppliers",
        ["supplier_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_bills_supplier_id_suppliers", "bills", type_="foreignkey")
    op.drop_index(op.f("ix_bills_supplier_id"), table_name="bills")
    op.drop_column("bills", "supplier_id")

    op.drop_index(op.f("ix_suppliers_email"), table_name="suppliers")
    op.drop_index(op.f("ix_suppliers_phone_number"), table_name="suppliers")
    op.drop_index(op.f("ix_suppliers_company_name"), table_name="suppliers")
    op.drop_index(op.f("ix_suppliers_supplier_name"), table_name="suppliers")
    op.drop_table("suppliers")
