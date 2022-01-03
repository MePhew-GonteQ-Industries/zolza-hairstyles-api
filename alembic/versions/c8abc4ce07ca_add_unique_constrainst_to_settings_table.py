"""Add unique constrainst to settings table

Revision ID: c8abc4ce07ca
Revises: 59f57aaec089
Create Date: 2022-01-03 10:40:46.920938

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8abc4ce07ca'
down_revision = '59f57aaec089'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('unique_user_settings', 'settings', ['user_id', 'name'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('unique_user_settings', 'settings')
    # ### end Alembic commands ###
