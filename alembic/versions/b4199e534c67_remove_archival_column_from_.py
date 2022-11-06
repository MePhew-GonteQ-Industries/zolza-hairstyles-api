"""Remove archival column from appointments table

Revision ID: b4199e534c67
Revises: 3b6341446c29
Create Date: 2022-11-06 18:01:57.636293

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b4199e534c67'
down_revision = '3b6341446c29'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('appointments', 'archival')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('appointments', sa.Column('archival', sa.BOOLEAN(), server_default=sa.text('false'), autoincrement=False, nullable=False))
    # ### end Alembic commands ###
