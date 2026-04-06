"""merge heads

Revision ID: b321f49e8ce9
Revises: 87334f3c7fda, create_low_stock_alerts
Create Date: 2026-02-02 08:46:42.852376

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b321f49e8ce9'
down_revision: Union[str, Sequence[str], None] = ('87334f3c7fda', 'create_low_stock_alerts')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
