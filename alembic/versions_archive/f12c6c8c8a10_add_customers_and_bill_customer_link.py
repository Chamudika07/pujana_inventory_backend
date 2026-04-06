"""add customers and bill customer link

Revision ID: f12c6c8c8a10
Revises: 0fed87c3fce1
Create Date: 2026-04-06 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f12c6c8c8a10"
down_revision: Union[str, Sequence[str], None] = "0fed87c3fce1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


customer_type_enum = sa.Enum("retail", "wholesale", "regular", "vip", name="customertype")


def upgrade() -> None:
    customer_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=30), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("customer_type", customer_type_enum, nullable=False, server_default="retail"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("loyalty_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("due_balance", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_customers_full_name"), "customers", ["full_name"], unique=False)
    op.create_index(op.f("ix_customers_phone_number"), "customers", ["phone_number"], unique=False)
    op.create_index(op.f("ix_customers_email"), "customers", ["email"], unique=False)

    op.add_column("bills", sa.Column("customer_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_bills_customer_id"), "bills", ["customer_id"], unique=False)
    op.create_foreign_key(
        "fk_bills_customer_id_customers",
        "bills",
        "customers",
        ["customer_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_bills_customer_id_customers", "bills", type_="foreignkey")
    op.drop_index(op.f("ix_bills_customer_id"), table_name="bills")
    op.drop_column("bills", "customer_id")

    op.drop_index(op.f("ix_customers_email"), table_name="customers")
    op.drop_index(op.f("ix_customers_phone_number"), table_name="customers")
    op.drop_index(op.f("ix_customers_full_name"), table_name="customers")
    op.drop_table("customers")

    customer_type_enum.drop(op.get_bind(), checkfirst=True)
