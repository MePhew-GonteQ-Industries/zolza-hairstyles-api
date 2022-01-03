"""Create settings table structure

Revision ID: 9d3349cb92bf
Revises: 165c026c31e4
Create Date: 2022-01-03 00:10:59.559513

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d3349cb92bf'
down_revision = '165c026c31e4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('settings', sa.Column('name', sa.String(), nullable=False))
    op.add_column('settings', sa.Column('default_value', sa.String(), nullable=False))
    op.add_column('settings', sa.Column('current_value', sa.String(), nullable=False))
    op.add_column('settings', sa.Column('last_updated', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('settings', sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('settings', 'created_at')
    op.drop_column('settings', 'last_updated')
    op.drop_column('settings', 'current_value')
    op.drop_column('settings', 'default_value')
    op.drop_column('settings', 'name')
    # ### end Alembic commands ###
