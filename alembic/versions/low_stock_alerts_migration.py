"""Create low stock alerts table and update users table

Revision ID: create_low_stock_alerts
Revises: 
Create Date: 2024-02-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'create_low_stock_alerts'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to users table
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))
    op.add_column('users', sa.Column('notification_email', sa.String(), nullable=True))
    op.add_column('users', sa.Column('notification_enabled', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('alert_threshold', sa.Integer(), nullable=False, server_default='5'))
    
    # Create low_stock_alerts table
    op.create_table(
        'low_stock_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('quantity_at_alert', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.String(), nullable=False),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_sent_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('next_alert_at', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop low_stock_alerts table
    op.drop_table('low_stock_alerts')
    
    # Remove columns from users table
    op.drop_column('users', 'alert_threshold')
    op.drop_column('users', 'notification_enabled')
    op.drop_column('users', 'notification_email')
    op.drop_column('users', 'phone_number')
