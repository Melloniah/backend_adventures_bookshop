from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision = '30d8815225ba'
down_revision = '939f215238b3'
branch_labels = None
depends_on = None

def upgrade():
    # Add 'location' column to orders
    op.add_column('orders', sa.Column('location', sa.Text(), nullable=False, server_default=""))

    # Drop old columns
    op.drop_column('orders', 'address')
    op.drop_column('orders', 'city')

    # Create order_status_logs table
    op.create_table(
        'order_status_logs',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('order_id', sa.Integer, sa.ForeignKey('orders.id', ondelete="CASCADE"), nullable=False),
        sa.Column('old_status', sa.String, nullable=False),
        sa.Column('new_status', sa.String, nullable=False),
        sa.Column('changed_at', sa.DateTime, default=datetime.utcnow),
        sa.Column('changed_by_admin_id', sa.Integer, sa.ForeignKey('users.id'), nullable=True),
    )

def downgrade():
    op.drop_table('order_status_logs')
    op.add_column('orders', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('orders', sa.Column('city', sa.String, nullable=True))
    op.drop_column('orders', 'location')
