"""Allow null values in default_value field in the settings table

Revision ID: 390305616fce
Revises: 139350e00ee6
Create Date: 2022-01-03 00:33:15.894571

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '390305616fce'
down_revision = '139350e00ee6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('settings', 'default_value',
               existing_type=sa.VARCHAR(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('settings', 'default_value',
               existing_type=sa.VARCHAR(),
               nullable=False)
    # ### end Alembic commands ###
