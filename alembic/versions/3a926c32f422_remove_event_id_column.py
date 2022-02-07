"""Remove event_id column

Revision ID: 3a926c32f422
Revises: 425dc77cbc41
Create Date: 2022-02-07 16:30:35.881839

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3a926c32f422'
down_revision = '425dc77cbc41'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('services_create_event_id_fkey', 'services', type_='foreignkey')
    op.drop_column('services', 'create_event_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('services', sa.Column('create_event_id', postgresql.UUID(), autoincrement=False, nullable=False))
    op.create_foreign_key('services_create_event_id_fkey', 'services', 'service_events', ['create_event_id'], ['id'])
    # ### end Alembic commands ###
