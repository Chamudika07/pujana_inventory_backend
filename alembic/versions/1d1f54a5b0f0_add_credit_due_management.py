"""add credit due management

Revision ID: 1d1f54a5b0f0
Revises: 0e7a99a1f214
Create Date: 2026-04-06 16:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "1d1f54a5b0f0"
down_revision: Union[str, Sequence[str], None] = "0e7a99a1f214"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


bill_payment_status = postgresql.ENUM("unpaid", "partially_paid", "paid", name="paymentstatus", create_type=False)
payment_direction = postgresql.ENUM("incoming", "outgoing", name="paymentdirection", create_type=False)
payment_type = postgresql.ENUM("customer_payment", "supplier_payment", "bill_initial_payment", name="paymenttype", create_type=False)
payment_method = postgresql.ENUM("cash", "card", "bank_transfer", "cheque", "other", name="paymentmethod", create_type=False)


def upgrade() -> None:
    postgresql.ENUM("unpaid", "partially_paid", "paid", name="paymentstatus").create(op.get_bind(), checkfirst=True)
    postgresql.ENUM("incoming", "outgoing", name="paymentdirection").create(op.get_bind(), checkfirst=True)
    postgresql.ENUM("customer_payment", "supplier_payment", "bill_initial_payment", name="paymenttype").create(op.get_bind(), checkfirst=True)
    postgresql.ENUM("cash", "card", "bank_transfer", "cheque", "other", name="paymentmethod").create(op.get_bind(), checkfirst=True)

    op.add_column("bills", sa.Column("subtotal_amount", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("bills", sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("bills", sa.Column("tax_amount", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("bills", sa.Column("total_amount", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("bills", sa.Column("paid_amount", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("bills", sa.Column("due_amount", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("bills", sa.Column("payment_status", bill_payment_status, nullable=False, server_default="unpaid"))
    op.add_column("bills", sa.Column("payment_mode_summary", sa.String(length=100), nullable=True))
    op.add_column("bills", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("bills", sa.Column("finalized_at", sa.TIMESTAMP(), nullable=True))
    op.add_column("bills", sa.Column("created_by", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_bills_created_by_users", "bills", "users", ["created_by"], ["id"], ondelete="SET NULL")
    op.create_index(op.f("ix_bills_bill_type"), "bills", ["bill_type"], unique=False)
    op.create_index(op.f("ix_bills_payment_status"), "bills", ["payment_status"], unique=False)
    op.create_index(op.f("ix_bills_created_by"), "bills", ["created_by"], unique=False)

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bill_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=True),
        sa.Column("supplier_id", sa.Integer(), nullable=True),
        sa.Column("payment_direction", payment_direction, nullable=False),
        sa.Column("payment_type", payment_type, nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("payment_method", payment_method, nullable=False, server_default="cash"),
        sa.Column("reference_number", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("paid_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["bill_id"], ["bills.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payments_bill_id"), "payments", ["bill_id"], unique=False)
    op.create_index(op.f("ix_payments_customer_id"), "payments", ["customer_id"], unique=False)
    op.create_index(op.f("ix_payments_supplier_id"), "payments", ["supplier_id"], unique=False)
    op.create_index(op.f("ix_payments_paid_at"), "payments", ["paid_at"], unique=False)
    op.create_index(op.f("ix_payments_created_at"), "payments", ["created_at"], unique=False)
    op.create_index(op.f("ix_payments_created_by"), "payments", ["created_by"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_payments_created_by"), table_name="payments")
    op.drop_index(op.f("ix_payments_created_at"), table_name="payments")
    op.drop_index(op.f("ix_payments_paid_at"), table_name="payments")
    op.drop_index(op.f("ix_payments_supplier_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_customer_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_bill_id"), table_name="payments")
    op.drop_table("payments")

    op.drop_index(op.f("ix_bills_created_by"), table_name="bills")
    op.drop_index(op.f("ix_bills_payment_status"), table_name="bills")
    op.drop_index(op.f("ix_bills_bill_type"), table_name="bills")
    op.drop_constraint("fk_bills_created_by_users", "bills", type_="foreignkey")
    op.drop_column("bills", "created_by")
    op.drop_column("bills", "finalized_at")
    op.drop_column("bills", "notes")
    op.drop_column("bills", "payment_mode_summary")
    op.drop_column("bills", "payment_status")
    op.drop_column("bills", "due_amount")
    op.drop_column("bills", "paid_amount")
    op.drop_column("bills", "total_amount")
    op.drop_column("bills", "tax_amount")
    op.drop_column("bills", "discount_amount")
    op.drop_column("bills", "subtotal_amount")

    postgresql.ENUM("cash", "card", "bank_transfer", "cheque", "other", name="paymentmethod").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM("customer_payment", "supplier_payment", "bill_initial_payment", name="paymenttype").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM("incoming", "outgoing", name="paymentdirection").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM("unpaid", "partially_paid", "paid", name="paymentstatus").drop(op.get_bind(), checkfirst=True)
