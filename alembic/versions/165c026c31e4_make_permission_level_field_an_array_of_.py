"""Make permission level field an array of strings

Revision ID: 165c026c31e4
Revises: bfba9da5d9d2
Create Date: 2022-01-02 21:25:02.839671

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '165c026c31e4'
down_revision = 'bfba9da5d9d2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'permission_level')
    op.add_column('users',  sa.Column('permission_level', sa.ARRAY(item_type=sa.String),
                                      nullable=False,
                                      server_default='{user}'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'permission_level')
    op.add_column('users', sa.Column('permission_level', sa.String(), server_default='user', nullable=False))
    # ### end Alembic commands ###
