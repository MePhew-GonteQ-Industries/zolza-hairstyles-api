"""Generate tables

Revision ID: de91e0420dcf
Revises: 
Create Date: 2022-02-27 19:26:47.542649

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'de91e0420dcf'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('surname', sa.String(), nullable=False),
    sa.Column('gender', sa.String(), nullable=False),
    sa.Column('permission_level', sa.ARRAY(sa.String()), server_default='{user}', nullable=False),
    sa.Column('verified', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('disabled', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('appointments',
    sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('service_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('scheduled_for', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('canceled', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('archival', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['service_id'], ['services.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('email_requests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('request_type', sa.String(), nullable=False),
    sa.Column('request_token', sa.String(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('passwords',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('password_hash', sa.String(), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('current', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('permission_events',
    sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('event_type', sa.String(), nullable=False),
    sa.Column('performed_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('performed_on_user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('performed_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['performed_by_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['performed_on_user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('service_events',
    sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('event_type', sa.String(), nullable=False),
    sa.Column('performed_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('performed_on_service_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('performed_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['performed_by_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['performed_on_service_id'], ['services.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('sessions',
    sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('access_token', sa.String(), nullable=False),
    sa.Column('refresh_token', sa.String(), nullable=False),
    sa.Column('sign_in_user_agent', sa.String(), nullable=False),
    sa.Column('sign_in_ip_address', sa.String(), nullable=False),
    sa.Column('last_user_agent', sa.String(), nullable=False),
    sa.Column('last_ip_address', sa.String(), nullable=False),
    sa.Column('last_accessed', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('sudo_mode_activated', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('sudo_mode_expires', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('first_accessed', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('settings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('default_value', sa.String(), nullable=True),
    sa.Column('current_value', sa.String(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('settings')
    op.drop_table('sessions')
    op.drop_table('service_events')
    op.drop_table('permission_events')
    op.drop_table('passwords')
    op.drop_table('email_requests')
    op.drop_table('appointments')
    op.drop_table('users')
    # ### end Alembic commands ###
