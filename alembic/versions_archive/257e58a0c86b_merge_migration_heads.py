"""merge migration heads

Revision ID: 257e58a0c86b
Revises: 57d3d5f433c9, 001_add_model_number_qr
Create Date: 2026-02-25 15:27:11.594915

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '257e58a0c86b'
down_revision: Union[str, Sequence[str], None] = ('57d3d5f433c9', '001_add_model_number_qr')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
