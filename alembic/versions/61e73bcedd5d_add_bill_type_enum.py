"""add bill type enum

Revision ID: 61e73bcedd5d
Revises: 257e58a0c86b
Create Date: 2026-03-06 02:21:16.976886
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Migration identifiers
revision: str = '61e73bcedd5d'
down_revision: Union[str, Sequence[str], None] = '257e58a0c86b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    
    # Create ENUM first
    billtype_enum = sa.Enum('buy', 'sell', name='billtype')
    billtype_enum.create(op.get_bind())

    # Add bill_code column
    op.add_column('bills', sa.Column('bill_code', sa.String(), nullable=True))

    # Fill existing rows
    op.execute("UPDATE bills SET bill_code = CONCAT('TEMP_', id)")

    # Make bill_code NOT NULL
    op.alter_column('bills', 'bill_code', nullable=False)

    # ⭐ Fix ENUM conversion (IMPORTANT PART)
    op.execute(
        "ALTER TABLE bills "
        "ALTER COLUMN bill_type TYPE billtype "
        "USING LOWER(bill_type)::billtype"
    )

    # Create index
    op.create_index(
        op.f('ix_bills_bill_code'),
        'bills',
        ['bill_code'],
        unique=True
    )


# ✅ Rollback migration
def downgrade() -> None:

    op.drop_index(op.f('ix_bills_bill_code'), table_name='bills')

    op.drop_column('bills', 'bill_code')

    # Drop enum type
    sa.Enum(name="billtype").drop(op.get_bind())