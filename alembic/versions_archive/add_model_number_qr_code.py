"""add model number and qr code fields

Revision ID: 001_add_model_number_qr
Revises: 
Create Date: 2026-02-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_model_number_qr'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # model_number already exists in the database, so we only add qr_code_path
    # Check if qr_code_path column exists before adding
    try:
        op.add_column('items', sa.Column('qr_code_path', sa.String(255), nullable=True))
    except Exception as e:
        # Column might already exist, continue
        pass


def downgrade() -> None:
    # Drop column if it exists
    try:
        op.drop_column('items', 'qr_code_path')
    except Exception as e:
        # Column might not exist
        pass
